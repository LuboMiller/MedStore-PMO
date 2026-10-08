"""Fireflies.ai GraphQL client (transcripts, summaries, audio URLs)."""

from __future__ import annotations

from typing import Any, Optional

import requests

from .config import Config
from .http import ApiError, bearer_session, raise_for_status

GRAPHQL_URL = "https://api.fireflies.ai/graphql"

TRANSCRIPT_LIST_FIELDS = """
  id
  title
  date
  dateString
  duration
  host_email
  organizer_email
  participants
  transcript_url
  meeting_link
"""

TRANSCRIPT_DETAIL_FIELDS = """
  id
  title
  date
  dateString
  duration
  host_email
  organizer_email
  participants
  transcript_url
  audio_url
  video_url
  meeting_link
  speakers { id name }
  meeting_attendees { displayName email name }
  sentences {
    index
    speaker_name
    speaker_id
    text
    raw_text
    start_time
    end_time
  }
  summary {
    keywords
    action_items
    outline
    shorthand_bullet
    overview
    bullet_gist
    gist
    short_summary
    short_overview
    meeting_type
    topics_discussed
    transcript_chapters
  }
"""


class FirefliesClient:
    def __init__(self, api_key: str, *, graphql_url: str = GRAPHQL_URL):
        self.api_key = api_key
        self.graphql_url = graphql_url.rstrip("/")
        self.session = bearer_session(api_key)

    @classmethod
    def from_config(cls, cfg: Config) -> "FirefliesClient":
        if not cfg.fireflies_ok:
            raise SystemExit("Missing FIREFLIES_API_KEY (Fireflies → Integrations → Fireflies API)")
        return cls(cfg.fireflies_api_key, graphql_url=cfg.fireflies_graphql_url)

    def graphql(self, query: str, variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        r = self.session.post(
            self.graphql_url,
            json={"query": query, "variables": variables or {}},
            timeout=120,
        )
        raise_for_status("fireflies", r)
        payload = r.json() if r.content else {}
        errors = payload.get("errors") or []
        if errors:
            msg = "; ".join(
                e.get("message") if isinstance(e, dict) else str(e) for e in errors
            )
            raise ApiError("fireflies", r.status_code or 200, msg)
        return payload.get("data") or {}

    def ping(self) -> dict[str, Any]:
        data = self.graphql(
            """
            query {
              user {
                user_id
                email
                name
                num_transcripts
                is_admin
              }
            }
            """
        )
        return data.get("user") or {}

    def list_transcripts(
        self,
        *,
        limit: int = 50,
        skip: int = 0,
        keyword: Optional[str] = None,
        keyword_scope: str = "title",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        mine: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        """List transcripts. Dates: ISO-8601 e.g. 2026-09-01T00:00:00.000Z"""
        query = f"""
        query Transcripts(
          $limit: Int
          $skip: Int
          $keyword: String
          $scope: String
          $fromDate: DateTime
          $toDate: DateTime
          $mine: Boolean
        ) {{
          transcripts(
            limit: $limit
            skip: $skip
            keyword: $keyword
            scope: $scope
            fromDate: $fromDate
            toDate: $toDate
            mine: $mine
          ) {{
            {TRANSCRIPT_LIST_FIELDS}
          }}
        }}
        """
        variables: dict[str, Any] = {
            "limit": min(max(limit, 1), 50),
            "skip": max(skip, 0),
        }
        if keyword:
            variables["keyword"] = keyword
            variables["scope"] = keyword_scope or "title"
        if from_date:
            variables["fromDate"] = from_date
        if to_date:
            variables["toDate"] = to_date
        if mine is not None:
            variables["mine"] = mine

        data = self.graphql(query, variables)
        return list(data.get("transcripts") or [])

    def get_transcript(self, transcript_id: str) -> dict[str, Any]:
        data = self.graphql(
            f"""
            query Transcript($id: String!) {{
              transcript(id: $id) {{
                {TRANSCRIPT_DETAIL_FIELDS}
              }}
            }}
            """,
            {"id": transcript_id},
        )
        tr = data.get("transcript")
        if not tr:
            raise ApiError("fireflies", 404, f"transcript not found: {transcript_id}")
        return tr

    def download_audio(self, audio_url: str, dest) -> int:
        """Download mp3/audio bytes to dest path. Returns bytes written."""
        from pathlib import Path

        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # audio_url is a short-lived signed URL — no Fireflies bearer needed
        r = requests.get(audio_url, timeout=300, stream=True)
        if not r.ok:
            raise ApiError("fireflies-audio", r.status_code, r.text[:400])
        size = 0
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
        return size
