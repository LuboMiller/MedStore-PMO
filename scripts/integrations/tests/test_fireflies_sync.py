import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pmo_integrations.fireflies_sync import meeting_folder_name, pull_transcript


class FakeFirefliesClient:
    def __init__(self, transcript: dict) -> None:
        self.transcript = transcript

    def get_transcript(self, transcript_id: str) -> dict:
        assert transcript_id == self.transcript["id"]
        return self.transcript


class MeetingFolderNameTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.out_root = Path(self.tmp.name)
        self.transcript = {
            "id": "01M20FAEJ1W8X5DXTJ4KC8JBKB",
            "dateString": "2026-09-08T12:19:03.000Z",
            "title": '"Acme | Sync"',
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def add_folder(self, name: str, transcript_id: str) -> None:
        folder = self.out_root / name
        folder.mkdir()
        (folder / "fireflies-meta.json").write_text(
            json.dumps({"id": transcript_id}), encoding="utf-8"
        )

    def test_new_meeting_uses_readable_name_without_id_suffix(self) -> None:
        self.assertEqual(
            meeting_folder_name(self.transcript, out_root=self.out_root),
            "2026-09-08-acme-sync",
        )

    def test_reuses_legacy_readable_folder_by_transcript_id(self) -> None:
        self.add_folder("2026-09-08-acme-sync", self.transcript["id"])
        self.assertEqual(
            meeting_folder_name(self.transcript, out_root=self.out_root),
            "2026-09-08-acme-sync",
        )

    def test_suffixes_a_different_meeting_with_same_date_and_title(self) -> None:
        self.add_folder("2026-09-08-acme-sync", "another-transcript-id")
        self.assertEqual(
            meeting_folder_name(self.transcript, out_root=self.out_root),
            "2026-09-08-acme-sync-4kc8jbkb",
        )

    def test_reuses_existing_collision_folder_by_transcript_id(self) -> None:
        self.add_folder("2026-09-08-acme-sync", "another-transcript-id")
        self.add_folder("2026-09-08-acme-sync-4kc8jbkb", self.transcript["id"])
        self.assertEqual(
            meeting_folder_name(self.transcript, out_root=self.out_root),
            "2026-09-08-acme-sync-4kc8jbkb",
        )

    def test_prefers_readable_folder_when_duplicate_same_id_exists(self) -> None:
        self.add_folder("2026-09-08-acme-sync", self.transcript["id"])
        self.add_folder("2026-09-08-acme-sync-4kc8jbkb", self.transcript["id"])
        self.assertEqual(
            meeting_folder_name(self.transcript, out_root=self.out_root),
            "2026-09-08-acme-sync",
        )

    def test_pull_skips_existing_readable_folder_without_creating_copy(self) -> None:
        self.add_folder("2026-09-08-acme-sync", self.transcript["id"])
        report = pull_transcript(
            FakeFirefliesClient(self.transcript),
            self.transcript["id"],
            out_root=self.out_root,
            download_audio=False,
        )
        self.assertTrue(report["skipped"])
        self.assertEqual(
            sorted(folder.name for folder in self.out_root.iterdir()),
            ["2026-09-08-acme-sync"],
        )


if __name__ == "__main__":
    unittest.main()
