import tempfile
import unittest
from pathlib import Path

from draft_core.draft_input import (
    DraftInputIntegrityError,
    validate_source_files,
)


class DraftInputIntegrityTests(unittest.TestCase):
    def test_accepts_existing_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "article.docx"
            source.touch()
            sections = [(1, "Section", [{"cleaned_path": str(source)}])]

            validate_source_files(sections, None)

    def test_reports_missing_source(self) -> None:
        missing = Path("missing-article.docx")
        sections = [(1, "Section", [{"cleaned_path": str(missing)}])]

        with self.assertRaises(DraftInputIntegrityError) as context:
            validate_source_files(sections, None)

        self.assertEqual(context.exception.missing_sources, [missing])
        self.assertIn(str(missing), str(context.exception))


if __name__ == "__main__":
    unittest.main()
