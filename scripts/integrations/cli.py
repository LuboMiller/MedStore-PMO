#!/usr/bin/env python3
"""CLI for mandatory PMO integrations (Confluence, Jira, Tempo) — REST API only.

Confluence (wave 3):
  python3 scripts/integrations/cli.py confluence bootstrap --space ACME --name "…"
  python3 scripts/integrations/cli.py confluence page-upsert --space ACME --title "…" --body-md "…"
  python3 scripts/integrations/cli.py confluence sync-pull --space ACME

Jira (wave 1):
  python3 scripts/integrations/cli.py jira bootstrap --key ACME --name "Acme Delivery"
  python3 scripts/integrations/cli.py jira sync-pull
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pmo_integrations.config import load_config  # noqa: E402
from pmo_integrations.confluence import ConfluenceClient  # noqa: E402
from pmo_integrations.health import run_health  # noqa: E402
from pmo_integrations.jira import JiraClient  # noqa: E402
from pmo_integrations.jira_agile import JiraAgileClient  # noqa: E402
from pmo_integrations.jira_company import (  # noqa: E402
    bootstrap_project,
    format_summary,
    validate_summary,
)
from pmo_integrations.jira_sync import (  # noqa: E402
    mark_dirty,
    maybe_auto_sync_issues,
    pull_issue,
    pull_project,
    push_project,
)
from pmo_integrations.tempo import TempoClient  # noqa: E402


def _print(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def cmd_health(_: argparse.Namespace) -> int:
    results = run_health()
    width = max(len(r.name) for r in results)
    failed = 0
    for r in results:
        if r.ok:
            mark = "✅"
        elif not r.required:
            mark = "⚠️"
        else:
            mark = "❌"
        print(f"{mark} {r.name.ljust(width)}  {r.detail}")
        if not r.ok and r.required:
            failed += 1
    if failed:
        print(f"\n{failed} required integration(s) failed. See scripts/integrations/README.md")
        return 1
    print("\nAll mandatory integrations OK.")
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    from pmo_integrations.model_router import (
        detect_environment,
        format_recommendation,
        policy_summary,
        recommend,
    )

    action = args.action
    if action == "env":
        env_id = detect_environment()
        payload = {"environment": env_id}
        if args.json:
            _print(payload)
        else:
            print(env_id)
        return 0
    if action == "policy":
        _print(policy_summary())
        return 0
    if action == "recommend":
        task = args.task
        if args.stdin or not task:
            if not sys.stdin.isatty():
                task = sys.stdin.read()
        if not (task or "").strip():
            raise SystemExit("--task or stdin required for models recommend")
        rec = recommend(task, environment=args.env, skill=args.skill)
        if args.json:
            _print(rec)
        else:
            print(format_recommendation(rec), end="")
        return 0
    raise SystemExit(f"Unknown models action: {action}")


def cmd_project(args: argparse.Namespace) -> int:
    from pmo_integrations.project_hydrate import hydrate_project

    cfg = load_config(require=("confluence",))
    jira_key = (args.jira_key or cfg.jira_project_key or "").upper()
    space = (args.space or cfg.confluence_space or "").upper()
    if not jira_key:
        raise SystemExit("--jira-key or JIRA_PROJECT_KEY required")
    if not space:
        raise SystemExit("--space or CONFLUENCE_DEFAULT_SPACE required")

    jira = JiraClient.from_config(cfg)
    jira.project_key = jira_key
    confluence = ConfluenceClient.from_config(cfg)

    if args.action == "hydrate":
        report = hydrate_project(
            jira=jira,
            confluence=confluence,
            jira_key=jira_key,
            space_key=space,
            sync_registries=not args.no_sync,
            seed_docs=not args.no_seed,
            update_context=not args.no_context,
            force=bool(args.force),
            dry_run=bool(args.dry_run),
        )
        _print(report)
        return 1 if report.get("errors") else 0
    raise SystemExit(f"Unknown project action: {args.action}")


def cmd_google(args: argparse.Namespace) -> int:
    from pmo_integrations.config import load_config
    from pmo_integrations.google_dirs import (
        ensure_example_copied,
        load_google_directories,
    )
    from pmo_integrations.google_workspace import (
        GoogleNotConfigured,
        GoogleWorkspaceClient,
        write_registry_index,
    )

    action = args.action

    if action == "init-dirs":
        path = ensure_example_copied()
        _print({"wrote": str(path), "hint": "Fill folder_id values, then: google directories"})
        return 0

    if action == "directories":
        cfg_dirs = load_google_directories(required=False)
        if cfg_dirs is None:
            _print(
                {
                    "directories": [],
                    "hint": "Run: python3 scripts/integrations/cli.py google init-dirs",
                }
            )
            return 0
        _print(
            {
                "default": cfg_dirs.default,
                "directories": [d.to_dict() for d in cfg_dirs.directories],
            }
        )
        return 0

    if action == "contracts-status":
        from datetime import date as date_cls

        from pmo_integrations.contracts import (
            build_status_report,
            ensure_example_copied,
        )

        if getattr(args, "init_contracts", False):
            path = ensure_example_copied()
            _print(
                {
                    "wrote": str(path),
                    "hint": "Fill CTR/STG dates, then: google contracts-status --write",
                }
            )
            return 0

        as_of = None
        if getattr(args, "as_of", None):
            as_of = date_cls.fromisoformat(args.as_of)
        cfg_path = Path(args.config) if getattr(args, "config", None) else None
        try:
            report = build_status_report(
                config_path=cfg_path,
                as_of=as_of,
                write=bool(getattr(args, "write", False)),
                snapshot=bool(getattr(args, "snapshot", False)),
            )
        except FileNotFoundError as e:
            raise SystemExit(
                f"{e}\nHint: python3 scripts/integrations/cli.py google contracts-status --init"
            ) from e
        _print(report)
        return 0

    if action == "auth":
        # Auth must work before google_ok (client secrets only).
        # Bare `google auth` → full PMO pack (Drive write + Sheets + Gmail) so a
        # Drive-only re-auth cannot silently wipe Sheets hydrate scopes again.
        want_sheets = bool(getattr(args, "sheets", False))
        want_sheets_ro = bool(getattr(args, "sheets_readonly", False))
        want_gmail = bool(getattr(args, "gmail", False))
        want_write = bool(getattr(args, "write_scope", False))
        if not any((want_sheets, want_sheets_ro, want_gmail, want_write)):
            want_sheets = True
            want_gmail = True
            want_write = True
        cfg = load_config()
        client = GoogleWorkspaceClient(
            auth_mode="oauth",
            credentials_path=cfg.google_credentials_path,
            oauth_client_secrets=cfg.google_oauth_client_secrets
            or "./secrets/google-oauth-client.json",
            oauth_token_path=cfg.google_oauth_token_path
            or "./secrets/google-oauth-token.json",
            folder_id=cfg.google_drive_folder_id,
            delegated_user=cfg.google_delegated_user,
        )
        try:
            _print(
                client.authorize_interactive(
                    readonly=not want_write and not want_sheets,
                    gmail=want_gmail,
                    sheets=want_sheets,
                    sheets_readonly=want_sheets_ro and not want_sheets,
                )
            )
        except GoogleNotConfigured as e:
            raise SystemExit(str(e)) from e
        return 0

    cfg = load_config(require=("google",))
    try:
        client = GoogleWorkspaceClient.from_config(cfg)
    except GoogleNotConfigured as e:
        raise SystemExit(str(e)) from e

    dirs_cfg = load_google_directories(required=False)

    def resolve_folder() -> tuple[str, str | None]:
        """Return (folder_id, dir_key)."""
        if args.folder_id:
            return args.folder_id, getattr(args, "dir", None)
        dir_key = getattr(args, "dir", None)
        if dir_key:
            if dirs_cfg is None:
                raise SystemExit(
                    "config/google-directories.json missing — run: google init-dirs"
                )
            d = dirs_cfg.get(dir_key)
            return d.folder_id, d.key
        if cfg.google_drive_folder_id:
            return cfg.google_drive_folder_id, None
        if dirs_cfg is not None:
            d = dirs_cfg.get()
            return d.folder_id, d.key
        raise SystemExit(
            "No folder: set --folder-id, --dir KEY, GOOGLE_DRIVE_FOLDER_ID, "
            "or config/google-directories.json"
        )

    if action == "ping":
        # Optionally bind default folder for sample listing
        try:
            folder_id, _ = resolve_folder()
            client.folder_id = folder_id
        except (SystemExit, ValueError, KeyError):
            pass
        _print(client.ping())
        return 0

    if action == "list":
        folder_id, dir_key = resolve_folder()
        files = client.list_folder(folder_id, page_size=args.limit or 50)
        _print({"dir": dir_key, "folder_id": folder_id, "count": len(files), "files": files})
        return 0

    if action == "sync-pull":
        if getattr(args, "all_dirs", False):
            if dirs_cfg is None:
                raise SystemExit("No google-directories.json — run: google init-dirs")
            results = []
            for d in dirs_cfg.directories:
                if not d.folder_id or d.folder_id.startswith("REPLACE"):
                    results.append({"key": d.key, "skipped": "folder_id not set"})
                    continue
                files = client.list_folder(d.folder_id, page_size=args.limit or 200)
                path = write_registry_index(files, folder_id=d.folder_id, dir_key=d.key)
                results.append(
                    {"key": d.key, "folder_id": d.folder_id, "count": len(files), "index": str(path)}
                )
            _print({"synced": results})
            return 0
        folder_id, dir_key = resolve_folder()
        files = client.list_folder(folder_id, page_size=args.limit or 200)
        path = write_registry_index(files, folder_id=folder_id, dir_key=dir_key)
        _print(
            {
                "dir": dir_key,
                "folder_id": folder_id,
                "count": len(files),
                "index": str(path),
            }
        )
        return 0

    if action == "export-doc":
        if not args.file_id:
            raise SystemExit("--file-id required")
        raw = client.export_google_doc(args.file_id, mime=args.mime or "text/plain")
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            _print({"wrote": args.out, "chars": len(text)})
        else:
            print(text)
        return 0

    if action == "export-sheets":
        from datetime import date as date_cls

        from pmo_integrations.sheets_hydrate import hydrate_client_status_sheet

        tabs = None
        if getattr(args, "tabs", None):
            tabs = [t.strip() for t in args.tabs.split(",") if t.strip()]
        out = Path(args.out) if args.out else None
        as_of = None
        if getattr(args, "as_of", None):
            as_of = date_cls.fromisoformat(args.as_of)
        try:
            report = hydrate_client_status_sheet(
                client,
                config_path=Path(args.config) if getattr(args, "config", None) else None,
                spreadsheet_id=args.file_id,
                out_dir=out,
                as_of=as_of,
                all_tabs=bool(getattr(args, "all_tabs", False)),
                tabs=tabs,
            )
        except (FileNotFoundError, ValueError) as e:
            raise SystemExit(str(e)) from e
        except Exception as e:  # noqa: BLE001
            err = str(e)
            if "insufficientPermissions" in err or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in err:
                raise SystemExit(
                    f"{e}\nRe-auth with Sheets read: "
                    "python3 scripts/integrations/cli.py google auth --sheets-readonly"
                ) from e
            raise SystemExit(str(e)) from e
        _print(report)
        return 1 if report.get("errors") else 0

    if action == "gmail-signature":
        try:
            info = client.get_gmail_signature(
                send_as_email=getattr(args, "send_as", None) or None
            )
        except GoogleNotConfigured as e:
            raise SystemExit(str(e)) from e
        except Exception as e:  # noqa: BLE001
            err = str(e)
            if "insufficientPermissions" in err or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in err:
                raise SystemExit(
                    f"{e}\nRe-auth with Gmail scopes: "
                    "python3 scripts/integrations/cli.py google auth --gmail"
                ) from e
            raise SystemExit(str(e)) from e
        preview = (info.get("signature_html") or "")[:500]
        _print({**info, "signature_preview": preview})
        return 0

    if action == "gmail-draft":
        from datetime import datetime, timezone

        from pmo_integrations.gmail_draft import (
            build_email_bodies,
            parse_weekly_status_email_md,
            resolve_recipients,
            want_append_signature,
            write_draft_registry,
        )

        if not args.file:
            raise SystemExit("--file required (e.g. docs/weekly-status/YYYY-MM-DD/email.md)")
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        if not file_path.exists():
            raise SystemExit(f"File not found: {file_path}")

        def _split_emails(raw: str | None) -> list[str]:
            if not raw:
                return []
            return [p.strip() for p in re.split(r"[,;]", raw) if p.strip()]

        mail_cfg = getattr(args, "mail_config", None)
        append_sig = want_append_signature(
            config_path=mail_cfg,
            cli_flag=False if getattr(args, "no_signature", False) else None,
        )
        send_as = getattr(args, "send_as", None) or None

        try:
            parsed = parse_weekly_status_email_md(file_path)
            to_list, cc_list = resolve_recipients(
                to=_split_emails(getattr(args, "to", None)),
                cc=_split_emails(getattr(args, "cc", None)),
                config_path=mail_cfg,
            )
        except ValueError as e:
            raise SystemExit(str(e)) from e

        subject = (getattr(args, "subject", None) or parsed.subject).strip()
        body = parsed.body
        if getattr(args, "dry_run", False):
            sig_meta: dict = {"append": append_sig, "fetched": False}
            sig_html = ""
            if append_sig:
                try:
                    sig_info = client.get_gmail_signature(send_as_email=send_as)
                    sig_html = sig_info.get("signature_html") or ""
                    sig_meta = {
                        "append": True,
                        "fetched": True,
                        "sendAsEmail": sig_info.get("sendAsEmail"),
                        "has_signature": bool(sig_html),
                        "signature_chars": len(sig_html),
                    }
                except Exception as e:  # noqa: BLE001
                    sig_meta = {
                        "append": True,
                        "fetched": False,
                        "error": str(e),
                        "hint": "python3 scripts/integrations/cli.py google auth --gmail",
                    }
            plain_out, html_out = build_email_bodies(body, signature_html=sig_html)
            _print(
                {
                    "dry_run": True,
                    "to": to_list,
                    "cc": cc_list,
                    "subject": subject,
                    "body_preview": plain_out[:400],
                    "body_chars": len(plain_out),
                    "html": bool(html_out),
                    "signature": sig_meta,
                    "file": str(file_path),
                }
            )
            return 0

        try:
            result = client.create_gmail_draft(
                to=to_list,
                cc=cc_list or None,
                subject=subject,
                body=body,
                append_signature=append_sig,
                send_as_email=send_as,
            )
        except GoogleNotConfigured as e:
            raise SystemExit(str(e)) from e
        except Exception as e:  # noqa: BLE001
            err = str(e)
            if "insufficientPermissions" in err or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in err:
                raise SystemExit(
                    f"{e}\nRe-auth with Gmail compose + settings: "
                    "python3 scripts/integrations/cli.py google auth --gmail"
                ) from e
            raise SystemExit(str(e)) from e

        record = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "local_file": str(file_path),
            "gmail": result,
            "status": "draft_created",
        }
        reg = write_draft_registry(record, slug=file_path.name)
        _print({**result, "registry": str(reg), "file": str(file_path)})
        return 0

    if action == "time-report":
        from pathlib import Path as _Path

        from pmo_integrations.time_report import prepare_monthly_act, result_to_dict

        month = getattr(args, "month", None)
        if not month:
            raise SystemExit("time-report requires --month YYYY-MM")
        cfg_path = _Path(args.config) if getattr(args, "config", None) else None
        try:
            result = prepare_monthly_act(
                month,
                cfg_path=cfg_path,
                dry_run=bool(getattr(args, "dry_run", False)),
                force=bool(getattr(args, "force", False)),
                create_if_missing=not bool(getattr(args, "no_create", False)),
            )
        except FileNotFoundError as e:
            raise SystemExit(str(e)) from e
        except GoogleNotConfigured as e:
            raise SystemExit(
                f"{e}\nRe-auth with Sheets + Drive write: "
                "python3 scripts/integrations/cli.py google auth --sheets --write-scope"
            ) from e
        except Exception as e:  # noqa: BLE001
            err = str(e)
            if "insufficientPermissions" in err or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in err:
                raise SystemExit(
                    f"{e}\nRe-auth with Sheets scopes: "
                    "python3 scripts/integrations/cli.py google auth --sheets --write-scope"
                ) from e
            raise SystemExit(str(e)) from e
        payload = result_to_dict(result)
        row_count = len(result.rows)
        payload.pop("rows", None)
        payload["row_count"] = row_count
        payload["rows_preview"] = [
            {
                "person": r.person,
                "work_title": r.work_title[:70],
                "hours": r.hours,
                "role": r.role,
                "cost": r.cost,
            }
            for r in result.rows[:8]
        ]
        _print(payload)
        return 0

    raise SystemExit(f"Unknown google action: {action}")


def cmd_fireflies(args: argparse.Namespace) -> int:
    from pmo_integrations.fireflies import FirefliesClient
    from pmo_integrations.fireflies_sync import pull_transcript, sync_pull

    action = args.action
    if action == "ping":
        cfg = load_config(require=("fireflies",))
        user = FirefliesClient.from_config(cfg).ping()
        _print(user)
        return 0

    if action == "list":
        cfg = load_config(require=("fireflies",))
        client = FirefliesClient.from_config(cfg)
        keyword = args.keyword if args.keyword is not None else (cfg.fireflies_keyword or None)
        rows = client.list_transcripts(
            limit=args.limit or 20,
            skip=args.skip or 0,
            keyword=keyword or None,
            keyword_scope=cfg.fireflies_keyword_scope or "title",
            from_date=args.from_date,
            to_date=args.to_date,
            mine=True if args.mine else None,
        )
        _print({"count": len(rows), "keyword": keyword, "transcripts": rows})
        return 0

    if action == "pull":
        if not args.id:
            raise SystemExit("fireflies pull requires --id <transcript_id>")
        cfg = load_config(require=("fireflies",))
        client = FirefliesClient.from_config(cfg)
        audio = False if args.no_audio else cfg.fireflies_download_audio
        report = pull_transcript(
            client,
            args.id,
            download_audio=audio,
            force=bool(args.force),
            dry_run=bool(args.dry_run),
        )
        _print(report)
        return 0 if report.get("ok") or report.get("skipped") or report.get("dry_run") else 1

    if action == "sync-pull":
        cfg = load_config(require=("fireflies",))
        audio = False if args.no_audio else None
        report = sync_pull(
            cfg,
            keyword=args.keyword,
            from_date=args.from_date,
            to_date=args.to_date,
            limit=args.limit or 50,
            download_audio=audio,
            force=bool(args.force),
            dry_run=bool(args.dry_run),
            mine=bool(args.mine),
        )
        _print(report)
        return 1 if report.get("errors") and not report.get("pulled") and not report.get("skipped") else 0

    raise SystemExit(f"Unknown fireflies action: {action}")


def cmd_repos(args: argparse.Namespace) -> int:

    from pmo_integrations.linked_repos import (
        discover_context,
        get_repo,
        list_repos,
        pull_all,
        push_repo,
        status_repo,
    )

    action = args.action
    if action == "list":
        _print(list_repos())
        return 0
    if action == "status":
        rows = []
        for row in list_repos():
            repo = get_repo(row["id"])
            if repo:
                rows.append(status_repo(repo))
        _print(rows)
        return 0
    if action == "discover":
        if not args.id:
            raise SystemExit("--id required")
        repo = get_repo(args.id)
        if not repo:
            raise SystemExit(f"Unknown repo id: {args.id}")
        _print(discover_context(repo))
        return 0
    if action == "pull":
        report = pull_all(kind=args.kind, repo_id=args.id, dry_run=bool(args.dry_run))
        _print(report)
        errs = [r for r in report.get("results") or [] if r.get("error")]
        return 1 if errs else 0
    if action == "push":
        if not args.id:
            raise SystemExit("--id required for push (safety)")
        repo = get_repo(args.id)
        if not repo:
            raise SystemExit(f"Unknown repo id: {args.id}")
        _print(push_repo(repo, message=args.message or "", dry_run=bool(args.dry_run)))
        return 0
    raise SystemExit(f"Unknown repos action: {action}")


def cmd_setup(args: argparse.Namespace) -> int:
    from pmo_integrations.setup_wizard import diagnose, run_wizard

    action = args.action
    if action == "status":
        diag = diagnose()
        _print(diag)
        return 1 if diag["missing"] else 0
    if action == "wizard":
        interactive = not bool(args.yes)
        report = run_wizard(
            interactive=interactive,
            install_google=bool(args.google),
            export_kb=bool(args.export_kb),
            skip_env_prompts=bool(args.skip_env),
        )
        _print(report.as_dict())
        failed = [s for s in report.steps if not s.ok and not s.skipped and s.id.startswith("req:")]
        return 1 if failed else 0
    raise SystemExit(f"Unknown setup action: {action}")


def cmd_confluence(args: argparse.Namespace) -> int:
    from pmo_integrations.confluence import markdown_to_storage
    from pmo_integrations.confluence_company import bootstrap_space
    from pmo_integrations.confluence_sync import mark_dirty, pull_space, push_space

    cfg = load_config(require=("confluence",))
    client = ConfluenceClient.from_config(cfg)
    action = args.action
    space = (args.space or cfg.confluence_space or "").upper()

    if action == "ping":
        _print(client.ping())
        return 0

    if action == "space":
        _print(client.get_space(space))
        return 0

    if action == "pages":
        pages = client.list_pages_by_key(space)
        for p in pages:
            print(f"{p.get('id')}\t{p.get('title')}")
        print(f"# total={len(pages)}", file=sys.stderr)
        return 0

    if action == "export":
        cmd = [sys.executable, str(ROOT / "scripts/confluence-export/export_pmo.py")]
        if args.space:
            cmd += ["--space", args.space]
        return subprocess.call(cmd)

    if action == "export-md":
        from pmo_integrations.confluence_md_export import DEFAULT_OUT_ROOT, export_space_markdown

        if not space:
            raise SystemExit("--space required for export-md (project space key)")
        report = export_space_markdown(
            space,
            out_root=DEFAULT_OUT_ROOT,
            client=client,
            sync_registry_first=bool(args.refresh),
            base_url=cfg.atlassian_base_url,
        )
        _print(report)
        return 0

    if action == "space-create":
        if not args.space or not args.name:
            raise SystemExit("--space and --name required")
        result = client.create_space(
            key=args.space,
            name=args.name,
            description=args.description or "",
            private=bool(args.private),
        )
        _print(result)
        return 0

    if action == "bootstrap":
        if not args.space or not args.name:
            raise SystemExit("--space and --name required")
        result = bootstrap_space(
            client,
            space_key=args.space,
            space_name=args.name,
            create_space=not args.existing_space,
            project_name=args.project_name or args.name,
            jira_key=args.jira_key or "",
            pm_name=args.pm or "",
            dm_name=args.dm or "",
            private=bool(args.private),
        )
        _print(result)
        return 0

    if action == "page-get":
        if args.page_id:
            _print(client.get_page(args.page_id))
            return 0
        if args.title:
            page = client.find_page_by_title(space, args.title)
            if not page:
                raise SystemExit(f"Page not found: {args.title}")
            _print(client.get_page(page["id"]))
            return 0
        raise SystemExit("--page-id or --title required")

    if action == "page-create":
        if not args.title:
            raise SystemExit("--title required")
        body = args.body_storage
        if body is None and args.body_md is not None:
            body = markdown_to_storage(args.body_md)
        if body is None and args.file:
            text = Path(args.file).read_text(encoding="utf-8")
            body = text if args.storage else markdown_to_storage(text)
        body = body or "<p></p>"
        result = client.create_page(
            space,
            args.title,
            body,
            parent_id=args.parent_id,
            parent_title=args.parent_title,
        )
        _print(result)
        return 0

    if action == "page-update" or action == "page-upsert":
        if not args.title and not args.page_id:
            raise SystemExit("--title or --page-id required")
        body = args.body_storage
        if body is None and args.body_md is not None:
            body = markdown_to_storage(args.body_md)
        if body is None and args.file:
            text = Path(args.file).read_text(encoding="utf-8")
            body = text if args.storage else markdown_to_storage(text)
        if body is None:
            raise SystemExit("Provide --body-md / --body-storage / --file")

        if action == "page-upsert" or (args.title and not args.page_id):
            result = client.upsert_page(
                space,
                args.title,
                body,
                parent_id=args.parent_id,
                parent_title=args.parent_title,
            )
            _print(result)
            return 0

        page = client.get_page(args.page_id)
        result = client.update_page(
            page,
            title=args.title,
            body_storage=body,
            parent_id=args.parent_id,
        )
        _print(result)
        return 0

    if action == "sync-pull":
        report = pull_space(client, space, export_md=not bool(getattr(args, "no_md", False)))
        _print(report)
        return 1 if report.get("errors") else 0

    if action == "sync-push":
        report = push_space(client, space, dry_run=bool(args.dry_run))
        _print(report)
        return 1 if report.get("errors") else 0

    if action == "registry-edit":
        record = mark_dirty(
            space,
            page_id=args.page_id,
            title=args.title,
            body_md=args.body_md,
            body_storage=args.body_storage,
            new_title=args.new_title,
        )
        _print(record)
        return 0

    raise SystemExit(f"Unknown confluence action: {action}")


def cmd_jira(args: argparse.Namespace) -> int:
    action = args.action
    # Actions that only need Atlassian creds (project create before key is in .env)
    need_project = action not in {
        "myself",
        "project-create",
        "bootstrap",
        "types",
    }
    cfg = load_config(require=("jira",) if need_project else ("confluence",))
    jira = JiraClient.from_config(cfg)
    if args.project:
        jira.project_key = args.project.upper()
    agile = JiraAgileClient.from_config(cfg)

    if action == "myself":
        _print(jira.myself())
        return 0

    if action == "types":
        key = args.project or cfg.jira_project_key
        for t in jira.list_issue_types(key):
            print(f"{t.get('id')}\t{t.get('name')}\t{'subtask' if t.get('subtask') else ''}")
        return 0

    if action == "issue":
        if not args.key:
            raise SystemExit("--key required")
        _print(jira.get_issue(args.key))
        return 0

    if action == "search" or action == "filter":
        jql = args.jql
        if not jql and action == "filter":
            raise SystemExit("--jql required for filter")
        if not jql:
            raise SystemExit("--jql required")
        for issue in jira.search(jql):
            f = issue.get("fields") or {}
            status = (f.get("status") or {}).get("name")
            print(f"{issue.get('key')}\t{status}\t{f.get('summary')}")
        return 0

    if action == "status-counts":
        counts = jira.status_counts()
        for name, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            print(f"{n:5d}  {name}")
        return 0

    if action == "project-create":
        if not args.project or not args.name:
            raise SystemExit("--project and --name required")
        lead = None
        if args.assignee:
            lead = jira.find_account_id(args.assignee)
        result = jira.create_project(key=args.project, name=args.name, lead_account_id=lead)
        _print(result)
        return 0

    if action == "bootstrap":
        if not args.project or not args.name:
            raise SystemExit("--project and --name required")
        result = bootstrap_project(
            jira,
            agile,
            project_key=args.project,
            project_name=args.name,
            create_project=not args.existing_project,
            board_name=args.board_name,
            first_sprint_name=args.sprint_name or "Sprint 1",
            lead=args.assignee,
        )
        _print(result)
        return 0

    if action == "create":
        if not args.type or not args.summary:
            raise SystemExit("--type and --summary required")
        summary = args.summary
        if args.kind:
            # Build summary from Devlight naming helpers when flags provided
            kwargs = {
                "name": args.summary,
                "n": args.number or 1,
                "epic": args.epic_num or 1,
                "story": args.story_num or 1,
                "role": args.role or "BE",
            }
            summary = format_summary(args.kind, **kwargs)
            for w in validate_summary(args.kind, summary):
                print(f"⚠️  {w}", file=sys.stderr)
        result = jira.create_issue(
            summary=summary,
            issuetype=args.type,
            description=args.description,
            assignee=args.assignee,
            parent_key=args.parent,
            labels=args.labels.split(",") if args.labels else None,
            priority=args.priority,
            project_key=args.project,
        )
        _print(result)
        created_key = result.get("key") if isinstance(result, dict) else None
        if created_key:
            maybe_auto_sync_issues(jira, created_key, project_key=args.project or jira.project_key)
        return 0

    if action == "transition":
        if not args.key or not args.status:
            raise SystemExit("--key and --status required")
        jira.transition(args.key, args.status, comment=args.comment)
        print(f"✅ {args.key} → {args.status}")
        maybe_auto_sync_issues(jira, args.key, project_key=args.project or jira.project_key)
        return 0

    if action == "assign":
        if not args.key or not args.assignee:
            raise SystemExit("--key and --assignee required")
        jira.assign(args.key, args.assignee)
        print(f"✅ {args.key} assigned to {args.assignee}")
        maybe_auto_sync_issues(jira, args.key, project_key=args.project or jira.project_key)
        return 0

    if action == "transitions":
        if not args.key:
            raise SystemExit("--key required")
        for t in jira.get_transitions(args.key):
            print(f"{t.get('id')}\t{t.get('name')}\t→ {(t.get('to') or {}).get('name')}")
        return 0

    if action == "boards":
        key = args.project or jira.project_key
        for b in agile.list_boards(project_key=key):
            print(f"{b.get('id')}\t{b.get('type')}\t{b.get('name')}")
        return 0

    if action == "board-create":
        key = args.project or jira.project_key
        if not args.name:
            raise SystemExit("--name required")
        result = agile.create_board(
            name=args.name,
            project_key=key,
            board_type=args.board_type or "scrum",
        )
        _print(result)
        return 0

    if action == "board-config":
        if not args.board_id:
            raise SystemExit("--board-id required")
        _print(agile.get_board_configuration(args.board_id))
        return 0

    if action == "sprints":
        if not args.board_id:
            # pick first board for project
            key = args.project or jira.project_key
            boards = agile.list_boards(project_key=key)
            if not boards:
                raise SystemExit("No boards found; pass --board-id")
            args.board_id = int(boards[0]["id"])
        for s in agile.list_sprints(args.board_id, state=args.sprint_state):
            print(f"{s.get('id')}\t{s.get('state')}\t{s.get('name')}")
        return 0

    if action == "sprint-create":
        if not args.board_id or not args.name:
            raise SystemExit("--board-id and --name required")
        result = agile.create_sprint(
            name=args.name,
            board_id=args.board_id,
            start_date=args.start,
            end_date=args.end,
            goal=args.goal or "",
        )
        _print(result)
        return 0

    if action == "sprint-start":
        if not args.sprint_id:
            raise SystemExit("--sprint-id required")
        _print(agile.start_sprint(args.sprint_id, start_date=args.start, end_date=args.end))
        return 0

    if action == "sprint-complete":
        if not args.sprint_id:
            raise SystemExit("--sprint-id required")
        _print(agile.complete_sprint(args.sprint_id))
        return 0

    if action == "sprint-add":
        if not args.sprint_id or not args.keys:
            raise SystemExit("--sprint-id and --keys required (comma-separated)")
        agile.move_issues_to_sprint(args.sprint_id, [k.strip() for k in args.keys.split(",")])
        print(f"✅ moved {args.keys} → sprint {args.sprint_id}")
        maybe_auto_sync_issues(
            jira,
            [k.strip() for k in args.keys.split(",") if k.strip()],
            project_key=args.project or jira.project_key,
        )
        return 0

    if action == "sync-pull":
        report = pull_project(jira, agile, project_key=args.project or jira.project_key)
        _print(report.as_dict())
        # Soft errors (e.g. kanban board without sprints) shouldn't fail the pull
        hard = [e for e in (report.errors or []) if "does not support sprints" not in e]
        return 1 if hard else 0

    if action == "sync-issue":
        if not args.key and not args.keys:
            raise SystemExit("--key or --keys required")
        keys: list[str] = []
        if args.key:
            keys.append(args.key)
        if args.keys:
            keys.extend(k.strip() for k in args.keys.split(",") if k.strip())
        from pmo_integrations.jira_sync import pull_issues

        report = pull_issues(jira, keys, project_key=args.project or jira.project_key)
        _print(report.as_dict())
        return 1 if report.errors else 0

    if action == "sync-push":
        report = push_project(
            jira,
            project_key=args.project or jira.project_key,
            dry_run=bool(args.dry_run),
        )
        _print(report.as_dict())
        return 1 if report.errors else 0

    if action == "registry-edit":
        if not args.key:
            raise SystemExit("--key required")
        updates = {}
        if args.status:
            updates["status"] = args.status
        if args.summary:
            updates["summary"] = args.summary
        if args.assignee:
            account_id = jira.find_account_id(args.assignee) or args.assignee
            updates["assignee_account_id"] = account_id
            updates["assignee_display"] = args.assignee
        if args.labels is not None:
            updates["labels"] = [x for x in args.labels.split(",") if x]
        if not updates:
            raise SystemExit("Nothing to edit; pass --status/--summary/--assignee/--labels")
        key = args.project or jira.project_key
        record = mark_dirty(key, args.key, updates)
        _print(record)
        return 0

    raise SystemExit(f"Unknown jira action: {action}")


def cmd_tempo(args: argparse.Namespace) -> int:
    from pmo_integrations.tempo_planning import (
        hours_to_seconds,
        planning_matrix,
    )
    from pmo_integrations.tempo_sync import (
        pull_period,
        push_local,
        save_local_plan,
        save_local_worklog,
    )

    cfg = load_config(require=("tempo",))
    client = TempoClient.from_config(cfg)
    action = args.action

    if action == "ping":
        print(json.dumps(client.ping(), ensure_ascii=False, indent=2)[:2000])
        return 0

    if action == "worklogs":
        if not args.from_date or not args.to_date:
            raise SystemExit("--from and --to required (YYYY-MM-DD)")
        logs = list(
            client.worklogs(
                from_date=args.from_date,
                to_date=args.to_date,
                project_id=args.project_id,
                issue_id=args.issue_id,
            )
        )
        if args.summary:
            _print(client.summarize_hours(logs))
        else:
            _print(logs)
        print(f"# worklogs={len(logs)}", file=sys.stderr)
        return 0

    if action == "log":
        # fact (+ optional bill)
        if not args.issue_id or not args.date or args.hours is None:
            raise SystemExit("--issue-id --date --hours required")
        fact_s = hours_to_seconds(args.hours)
        bill_s = None
        if args.bill_hours is not None:
            bill_s = hours_to_seconds(args.bill_hours)
        elif args.non_billable:
            bill_s = 0
        result = client.create_worklog(
            issue_id=args.issue_id,
            time_spent_seconds=fact_s,
            start_date=args.date,
            start_time=args.start_time or "09:00:00",
            billable_seconds=bill_s,
            description=args.description or "",
            author_account_id=args.account_id,
        )
        _print(result)
        return 0

    if action == "log-draft":
        if not args.issue_id or not args.date or args.hours is None:
            raise SystemExit("--issue-id --date --hours required")
        fact_s = hours_to_seconds(args.hours)
        bill_s = hours_to_seconds(args.bill_hours) if args.bill_hours is not None else (
            0 if args.non_billable else None
        )
        draft = {
            "issue_id": args.issue_id,
            "time_spent_seconds": fact_s,
            "billable_seconds": bill_s,
            "start_date": args.date,
            "start_time": args.start_time or "09:00:00",
            "description": args.description or "",
            "author_account_id": args.account_id,
        }
        path = save_local_worklog(draft, slug=args.slug)
        print(f"✅ draft worklog → {path}")
        return 0

    if action == "plans":
        if not args.from_date or not args.to_date:
            raise SystemExit("--from and --to required")
        account_ids = args.account_id.split(",") if args.account_id else None
        plans = list(
            client.search_plans(
                from_date=args.from_date,
                to_date=args.to_date,
                account_ids=account_ids,
                project_ids=[int(args.project_id)]
                if args.project_id and str(args.project_id).isdigit()
                else None,
            )
        )
        if args.summary:
            _print(client.summarize_plans(plans))
        else:
            _print(plans)
        print(f"# plans={len(plans)}", file=sys.stderr)
        return 0

    if action == "plan":
        if not args.account_id or not args.start or not args.end or args.hours is None:
            raise SystemExit("--account-id --start --end --hours (per day) required")
        result = client.create_plan(
            account_id=args.account_id,
            start=args.start,
            end=args.end,
            planned_seconds_per_day=hours_to_seconds(args.hours),
            plan_item_type=args.plan_item_type or "ISSUE",
            plan_item_id=args.issue_id or args.plan_item_id,
            description=args.description or "",
        )
        _print(result)
        return 0

    if action == "plan-draft":
        if not args.account_id or not args.start or not args.end or args.hours is None:
            raise SystemExit("--account-id --start --end --hours required")
        draft = {
            "account_id": args.account_id,
            "start": args.start,
            "end": args.end,
            "planned_seconds_per_day": hours_to_seconds(args.hours),
            "plan_item_type": args.plan_item_type or "ISSUE",
            "plan_item_id": args.issue_id or args.plan_item_id,
            "description": args.description or "",
        }
        path = save_local_plan(draft, slug=args.slug)
        print(f"✅ draft plan → {path}")
        return 0

    if action == "plan-delete":
        if not args.plan_id:
            raise SystemExit("--plan-id required")
        client.delete_plan(args.plan_id)
        print(f"✅ deleted plan {args.plan_id}")
        return 0

    if action == "overlaps" or action == "matrix":
        if not args.from_date or not args.to_date:
            raise SystemExit("--from and --to required")
        account_ids = args.account_id.split(",") if args.account_id else None
        plans = list(
            client.search_plans(
                from_date=args.from_date,
                to_date=args.to_date,
                account_ids=account_ids,
            )
        )
        worklogs = list(
            client.worklogs(
                from_date=args.from_date,
                to_date=args.to_date,
                project_id=args.project_id,
            )
        )
        capacity = hours_to_seconds(args.capacity_hours) if args.capacity_hours else 8 * 3600
        matrix = planning_matrix(plans, worklogs, capacity_seconds=capacity)
        _print(matrix)
        return 0 if matrix["overlap_count"] == 0 or action == "matrix" else 2

    if action == "sync-pull":
        if not args.from_date or not args.to_date:
            raise SystemExit("--from and --to required")
        report = pull_period(
            client,
            from_date=args.from_date,
            to_date=args.to_date,
            project_id=args.project_id,
            account_ids=args.account_id.split(",") if args.account_id else None,
        )
        _print(report)
        return 0

    if action == "sync-push":
        report = push_local(client, dry_run=bool(args.dry_run))
        _print(report)
        return 1 if report.get("errors") else 0

    raise SystemExit(f"Unknown tempo action: {action}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="PMO integrations CLI (Confluence / Jira / Tempo / Google / Fireflies)")
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("health", help="Check Confluence + Jira + Tempo (+ optional Google / Fireflies)")
    h.set_defaults(func=cmd_health)

    m = sub.add_parser("models", help="Portable model orchestrator (Cursor / Claude / Codex / VS Code)")
    m.add_argument("action", choices=["recommend", "policy", "env"])
    m.add_argument("--task", default=None, help="User request / skill name to classify")
    m.add_argument("--skill", default=None, help="Explicit pmo-* skill id")
    m.add_argument(
        "--env",
        dest="env",
        default=None,
        choices=["cursor", "claude", "codex", "vscode_claude", "generic"],
        help="Override auto-detected IDE",
    )
    m.add_argument("--stdin", action="store_true", help="Read task text from stdin")
    m.add_argument("--json", action="store_true")
    m.set_defaults(func=cmd_models)

    s = sub.add_parser("setup", help="First-run wizard: deps, .env, linked repos, health")
    s.add_argument("action", choices=["wizard", "status"])
    s.add_argument("--yes", action="store_true", help="Non-interactive (no prompts)")
    s.add_argument("--google", action="store_true", help="Install Google API packages")
    s.add_argument("--export-kb", action="store_true", help="Export Confluence PMO KB")
    s.add_argument("--skip-env", action="store_true", help="Do not prompt for .env values")
    s.set_defaults(func=cmd_setup)

    proj = sub.add_parser("project", help="Hydrate local repo from existing Atlassian project")
    proj.add_argument("action", choices=["hydrate"])
    proj.add_argument("--jira-key", default=None)
    proj.add_argument("--space", default=None, help="Confluence space key")
    proj.add_argument("--no-sync", action="store_true", help="Skip registry sync-pull")
    proj.add_argument("--no-seed", action="store_true", help="Do not write local doc stubs")
    proj.add_argument("--no-context", action="store_true", help="Do not patch CONTEXT.md")
    proj.add_argument("--force", action="store_true", help="Overwrite existing seeded docs")
    proj.add_argument("--dry-run", action="store_true")
    proj.set_defaults(func=cmd_project)

    g = sub.add_parser("google", help="Google Workspace (Drive / Docs / Sheets / Gmail drafts) — wave 4")
    g.add_argument(
        "action",
        choices=[
            "auth",
            "init-dirs",
            "directories",
            "ping",
            "list",
            "sync-pull",
            "export-doc",
            "export-sheets",
            "contracts-status",
            "gmail-signature",
            "gmail-draft",
            "time-report",
        ],
    )
    g.add_argument("--folder-id", default=None, help="Raw Drive folder ID")
    g.add_argument(
        "--dir",
        default=None,
        dest="dir",
        help="Named directory key from config/google-directories.json",
    )
    g.add_argument(
        "--all-dirs",
        action="store_true",
        help="sync-pull: all directories from google-directories.json",
    )
    g.add_argument("--file-id", default=None)
    g.add_argument("--out", default=None, help="Output path for export-doc / export-sheets")
    g.add_argument("--mime", default=None, help="Export MIME (default text/plain)")
    g.add_argument("--limit", type=int, default=None)
    g.add_argument(
        "--tabs",
        default=None,
        help="export-sheets: comma-separated tab titles (default from config daily_tabs)",
    )
    g.add_argument(
        "--all-tabs",
        action="store_true",
        help="export-sheets: export every tab (heavy; skip for daily)",
    )
    g.add_argument(
        "--as-of",
        default=None,
        dest="as_of",
        help="export-sheets: date YYYY-MM-DD for out_dir template (default today)",
    )
    g.add_argument(
        "--write-scope",
        action="store_true",
        help="auth: request full drive scope (default readonly)",
    )
    g.add_argument(
        "--gmail",
        action="store_true",
        help="auth: request gmail.compose + gmail.settings.basic (drafts + signature)",
    )
    g.add_argument(
        "--sheets",
        action="store_true",
        help="auth: request spreadsheets + drive write (time-report create/fill)",
    )
    g.add_argument(
        "--sheets-readonly",
        action="store_true",
        dest="sheets_readonly",
        help="auth: request spreadsheets.readonly (daily export-sheets hydrate)",
    )
    g.add_argument(
        "--month",
        default=None,
        help="time-report: period YYYY-MM (Tempo bill → Time Report sheet tab)",
    )
    g.add_argument(
        "--config",
        default=None,
        help="time-report / contracts-status: path to config JSON (defaults under config/)",
    )
    g.add_argument(
        "--write",
        action="store_true",
        help="contracts-status: write docs/contracts/register.md",
    )
    g.add_argument(
        "--snapshot",
        action="store_true",
        help="contracts-status: also write docs/contracts/status-YYYY-MM-DD.md",
    )
    g.add_argument(
        "--init",
        action="store_true",
        dest="init_contracts",
        help="contracts-status: copy contracts.example.json → config/contracts.json",
    )
    g.add_argument(
        "--force",
        action="store_true",
        help="time-report: overwrite non-empty month tab",
    )
    g.add_argument(
        "--no-create",
        action="store_true",
        help="time-report: fail if spreadsheet missing (do not create)",
    )
    g.add_argument(
        "--file",
        default=None,
        help="gmail-draft: path to email markdown (docs/weekly-status/YYYY-MM-DD/email.md)",
    )
    g.add_argument("--to", default=None, help="gmail-draft: comma-separated To emails")
    g.add_argument("--cc", default=None, help="gmail-draft: comma-separated Cc emails")
    g.add_argument("--subject", default=None, help="gmail-draft: override subject")
    g.add_argument(
        "--mail-config",
        default=None,
        help="gmail-draft: path to weekly-status-mail.json (default config/)",
    )
    g.add_argument(
        "--send-as",
        default=None,
        dest="send_as",
        help="gmail-draft/signature: sendAs email alias (default: Gmail isDefault)",
    )
    g.add_argument(
        "--no-signature",
        action="store_true",
        help="gmail-draft: do not append Gmail Settings signature",
    )
    g.add_argument(
        "--dry-run",
        action="store_true",
        help="gmail-draft: parse and show payload without creating a draft",
    )
    g.set_defaults(func=cmd_google)

    ff = sub.add_parser("fireflies", help="Fireflies.ai transcripts / summaries / audio")
    ff.add_argument("action", choices=["ping", "list", "pull", "sync-pull"])
    ff.add_argument("--id", default=None, help="Transcript id for pull")
    ff.add_argument("--keyword", default=None, help="Filter by keyword (overrides FIREFLIES_KEYWORD)")
    ff.add_argument("--from-date", default=None, dest="from_date", help="ISO date e.g. 2026-09-01T00:00:00.000Z")
    ff.add_argument("--to-date", default=None, dest="to_date", help="ISO date e.g. 2026-09-30T23:59:59.000Z")
    ff.add_argument("--limit", type=int, default=None)
    ff.add_argument("--skip", type=int, default=0)
    ff.add_argument("--mine", action="store_true", help="Only meetings for API key owner")
    ff.add_argument("--force", action="store_true", help="Overwrite existing meeting folder")
    ff.add_argument("--no-audio", action="store_true", help="Skip audio.mp3 download")
    ff.add_argument("--dry-run", action="store_true")
    ff.set_defaults(func=cmd_fireflies)

    r = sub.add_parser("repos", help="Optional linked BA / codebase repositories")
    r.add_argument("action", choices=["list", "status", "pull", "push", "discover"])
    r.add_argument("--id", default=None, help="Repo id from config/linked-repos.json")
    r.add_argument("--kind", choices=["ba", "codebase"], default=None)
    r.add_argument("--message", default=None, help="Commit message for push")
    r.add_argument("--dry-run", action="store_true")
    r.set_defaults(func=cmd_repos)

    c = sub.add_parser("confluence", help="Confluence API + registry sync")
    c.add_argument(
        "action",
        choices=[
            "ping",
            "space",
            "pages",
            "export",
            "export-md",
            "space-create",
            "bootstrap",
            "page-get",
            "page-create",
            "page-update",
            "page-upsert",
            "sync-pull",
            "sync-push",
            "registry-edit",
        ],
    )
    c.add_argument("--space", default=None)
    c.add_argument("--name", default=None)
    c.add_argument("--description", default=None)
    c.add_argument("--title", default=None)
    c.add_argument("--new-title", default=None)
    c.add_argument("--page-id", default=None)
    c.add_argument("--parent-id", default=None)
    c.add_argument("--parent-title", default=None)
    c.add_argument("--body-md", default=None)
    c.add_argument("--body-storage", default=None)
    c.add_argument("--no-md", action="store_true", help="sync-pull: skip markdown hierarchy export")
    c.add_argument(
        "--refresh",
        action="store_true",
        help="export-md: re-pull registry from Confluence before writing markdown",
    )
    c.add_argument("--file", default=None)
    c.add_argument("--storage", action="store_true", help="Treat --file as storage HTML")
    c.add_argument("--project-name", default=None)
    c.add_argument("--jira-key", default=None)
    c.add_argument("--pm", default=None)
    c.add_argument("--dm", default=None)
    c.add_argument("--existing-space", action="store_true")
    c.add_argument("--private", action="store_true")
    c.add_argument("--dry-run", action="store_true")
    c.set_defaults(func=cmd_confluence)

    jira_actions = [
        "myself",
        "types",
        "issue",
        "search",
        "filter",
        "status-counts",
        "project-create",
        "bootstrap",
        "create",
        "transition",
        "transitions",
        "assign",
        "boards",
        "board-create",
        "board-config",
        "sprints",
        "sprint-create",
        "sprint-start",
        "sprint-complete",
        "sprint-add",
        "sync-pull",
        "sync-issue",
        "sync-push",
        "registry-edit",
    ]
    j = sub.add_parser("jira", help="Jira API + registry sync")
    j.add_argument("action", choices=jira_actions)
    j.add_argument("--project", default=None, help="Project key override")
    j.add_argument("--name", default=None)
    j.add_argument("--key", default=None, help="Issue key")
    j.add_argument("--keys", default=None, help="Comma-separated issue keys")
    j.add_argument("--jql", default=None)
    j.add_argument("--type", dest="type", default=None, help="Issue type name")
    j.add_argument("--summary", default=None)
    j.add_argument("--description", default=None)
    j.add_argument("--assignee", default=None)
    j.add_argument("--parent", default=None)
    j.add_argument("--labels", default=None)
    j.add_argument("--priority", default=None)
    j.add_argument("--status", default=None)
    j.add_argument("--comment", default=None)
    j.add_argument("--board-id", type=int, default=None)
    j.add_argument("--board-name", default=None)
    j.add_argument("--board-type", default=None)
    j.add_argument("--sprint-id", type=int, default=None)
    j.add_argument("--sprint-name", default=None)
    j.add_argument("--sprint-state", default=None)
    j.add_argument("--start", default=None, help="ISO datetime for sprint")
    j.add_argument("--end", default=None)
    j.add_argument("--goal", default=None)
    j.add_argument("--existing-project", action="store_true")
    j.add_argument("--dry-run", action="store_true")
    j.add_argument("--kind", choices=["epic", "story", "task", "subtask", "cr"], default=None)
    j.add_argument("--number", type=int, default=None)
    j.add_argument("--epic-num", type=int, default=None)
    j.add_argument("--story-num", type=int, default=None)
    j.add_argument("--role", default=None)
    j.set_defaults(func=cmd_jira)

    tempo_actions = [
        "ping",
        "worklogs",
        "log",
        "log-draft",
        "plans",
        "plan",
        "plan-draft",
        "plan-delete",
        "overlaps",
        "matrix",
        "sync-pull",
        "sync-push",
    ]
    t = sub.add_parser("tempo", help="Tempo Timesheets + Planner")
    t.add_argument("action", choices=tempo_actions)
    t.add_argument("--from", dest="from_date", default=None)
    t.add_argument("--to", dest="to_date", default=None)
    t.add_argument("--project-id", dest="project_id", default=None)
    t.add_argument("--issue-id", dest="issue_id", default=None)
    t.add_argument("--plan-item-id", dest="plan_item_id", default=None)
    t.add_argument("--plan-item-type", default=None)
    t.add_argument("--plan-id", type=int, default=None)
    t.add_argument("--account-id", default=None, help="Atlassian accountId (or comma-list)")
    t.add_argument("--hours", type=float, default=None, help="Hours (fact or plan-per-day)")
    t.add_argument("--bill-hours", type=float, default=None, help="Billable hours override")
    t.add_argument("--non-billable", action="store_true")
    t.add_argument("--date", default=None, help="Worklog date YYYY-MM-DD")
    t.add_argument("--start", default=None, help="Plan start YYYY-MM-DD")
    t.add_argument("--end", default=None, help="Plan end YYYY-MM-DD")
    t.add_argument("--start-time", default=None)
    t.add_argument("--description", default=None)
    t.add_argument("--capacity-hours", type=float, default=None, help="Daily capacity for overlaps")
    t.add_argument("--slug", default=None)
    t.add_argument("--summary", action="store_true")
    t.add_argument("--dry-run", action="store_true")
    t.set_defaults(func=cmd_tempo)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
