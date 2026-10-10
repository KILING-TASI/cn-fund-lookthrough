import tempfile
import unittest
from pathlib import Path
from tools.run_scenarios import run


class ScenarioCLI(unittest.TestCase):
    def test_reviewable_cli_batch_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'batch'
            receipt = run(out)
            self.assertTrue(all(row['passed'] for row in receipt['cases']))
            before = (out / 'receipt.json').read_bytes()
            with self.assertRaises(FileExistsError):
                run(out)
            self.assertEqual(before, (out / 'receipt.json').read_bytes())
