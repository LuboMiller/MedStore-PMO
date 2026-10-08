import sys
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pmo_integrations.model_router import ROOT, classify, detect_environment, recommend


class DetectEnvironmentTests(unittest.TestCase):
    def test_cursor_wins_over_vscode_pid(self):
        env = {"CURSOR_TRACE_ID": "abc", "VSCODE_PID": "1", "TERM_PROGRAM": "vscode"}
        self.assertEqual(detect_environment(env), "cursor")

    def test_claude_code(self):
        self.assertEqual(detect_environment({"CLAUDECODE": "1"}), "claude")

    def test_codex(self):
        self.assertEqual(detect_environment({"CODEX_HOME": "/tmp/codex"}), "codex")

    def test_vscode_claude(self):
        self.assertEqual(detect_environment({"VSCODE_PID": "99", "TERM_PROGRAM": "vscode"}), "vscode_claude")

    def test_generic(self):
        self.assertEqual(detect_environment({}), "generic")


class ClassifyTests(unittest.TestCase):
    def test_ews_is_reasoning(self):
        out = classify("Зроби EWS на цей понеділок, чесність важлива")
        self.assertEqual(out["tier"], "reasoning")

    def test_hydrate_is_long(self):
        out = classify("project hydrate from Jira and Confluence")
        self.assertEqual(out["tier"], "long")

    def test_daily_actions_standard(self):
        out = classify("що мені зробити сьогодні?")
        self.assertEqual(out["tier"], "standard")

    def test_path_lookup_fast(self):
        out = classify("де лежить CONTEXT.md?")
        self.assertEqual(out["tier"], "fast")

    def test_skill_qg_overrides_daily(self):
        out = classify("після daily actions прожени pmo-qg-review-wbs")
        self.assertEqual(out["tier"], "reasoning")
        self.assertIn("pmo-qg-review-wbs", out["skills"])

    def test_explicit_skill_arg(self):
        out = classify("go", skill="pmo-start-project")
        self.assertEqual(out["tier"], "long")


class RecommendTests(unittest.TestCase):
    def test_cursor_reasoning_slug(self):
        rec = recommend("EWS report", environment="cursor")
        self.assertEqual(rec["tier"], "reasoning")
        self.assertEqual(rec["action"], "spawn_subagent")
        self.assertIn("opus", rec["model"])

    def test_codex_routes_reasoning_to_subagent(self):
        rec = recommend("escalation memo", environment="codex")
        self.assertEqual(rec["action"], "spawn_subagent")
        self.assertEqual(rec["agent"], "pmo_reasoning")
        self.assertEqual(rec["model"], "gpt-5.6-sol")
        self.assertEqual(rec["extra"].get("model_reasoning_effort"), "high")

    def test_codex_fast_and_long_have_distinct_agents(self):
        fast = recommend("де лежить CONTEXT.md?", environment="codex")
        long = recommend("pmo-weekly-rhythm", environment="codex")
        self.assertEqual((fast["action"], fast["agent"], fast["model"]),
                         ("spawn_subagent", "pmo_fast", "gpt-5.6-luna"))
        self.assertEqual((long["action"], long["agent"], long["model"]),
                         ("spawn_subagent", "pmo_long", "gpt-6-astra"))

    def test_codex_agent_files_match_router_policy(self):
        for task in ("де лежить CONTEXT.md?", "daily actions", "EWS", "pmo-weekly-rhythm"):
            rec = recommend(task, environment="codex")
            path = ROOT / ".codex" / "agents" / f"{rec['agent']}.toml"
            with self.subTest(tier=rec["tier"]):
                agent = tomllib.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(agent["name"], rec["agent"])
                self.assertEqual(agent["model"], rec["model"])
                self.assertEqual(agent["model_reasoning_effort"],
                                 rec["extra"]["model_reasoning_effort"])
                self.assertTrue(agent["description"])
                self.assertTrue(agent["developer_instructions"])

    def test_claude_fast(self):
        rec = recommend("list skills", environment="claude")
        self.assertEqual(rec["tier"], "fast")
        self.assertEqual(rec["model"], "haiku")


if __name__ == "__main__":
    unittest.main()
