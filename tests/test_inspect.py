from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from control_promotion.inspect import check_ssot_links


class InspectTest(unittest.TestCase):
    def test_check_ssot_links_preserves_repo_relative_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "ssot" / "quality-ai-harness.md"
            target.parent.mkdir()
            target.write_text("# Quality Harness\n", encoding="utf-8")
            link = root / "develop" / "Harness" / "quality-ai-harness.md"
            link.parent.mkdir(parents=True)
            os.symlink(target, link)

            result = check_ssot_links(
                ["develop/Harness/quality-ai-harness.md"],
                project_root=root,
            )

        self.assertEqual(len(result["symlinks"]), 1)
        item = result["symlinks"][0]
        self.assertEqual(item["path"], "develop/Harness/quality-ai-harness.md")
        self.assertTrue(item["exists"])
        self.assertTrue(item["is_symlink"])
        self.assertEqual(item["target"], str(target))
        self.assertIn("SSOT ownership", item["recommendation"])


if __name__ == "__main__":
    unittest.main()
