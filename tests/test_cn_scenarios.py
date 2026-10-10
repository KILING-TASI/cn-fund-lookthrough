import copy
import json
from pathlib import Path
import tempfile
import unittest
from cnlookthrough.report_adapter import to_spec
from tools.run_scenarios import ROOT, run


class CNScenarios(unittest.TestCase):
    def test_cn_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = run(Path(tmp) / 'new', ROOT / 'examples/cn-scenarios/index.json')
            self.assertEqual(receipt['groups'], 3)
            self.assertTrue(all(row['passed'] for row in receipt['cases']))

    def test_missing_scope_and_renormalization_rejected_without_mutation(self):
        base = json.loads((ROOT / 'examples/cn-scenarios/complete-equity.json').read_text('utf-8'))
        for patch in ({'portfolioScope': None}, {'renormalized': True}):
            parsed = copy.deepcopy(base)
            parsed.update(patch)
            before = copy.deepcopy(parsed)
            with self.assertRaises(ValueError):
                to_spec(parsed, '2026-10-10')
            self.assertEqual(parsed, before)
