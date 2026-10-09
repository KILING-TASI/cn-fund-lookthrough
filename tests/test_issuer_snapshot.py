import copy
import unittest
from cnlookthrough.issuer_snapshot import apply_snapshot_mappings


class TestIssuerSnapshot(unittest.TestCase):
    def setUp(self):
        self.spec = {'asOf': '2026-04-01', 'nodes': {'fund': {'reportDate': '2025-12-31', 'holdings': [{'security': 'CN-equity:300308'}]}},
                     'securities': {'CN-equity:300308': {'kind': 'stock', 'issuer': None}}}
        self.mapping = {'inputSchema': 'issuer-snapshot-map-v1', 'methodVersion': 'source-bound-snapshot-1',
                        'mappings': [{'security': 'CN-equity:300308', 'code': '300308', 'issuerName': 'Teaching Issuer',
                                      'validFrom': '2025-12-31', 'validUntil': '2025-12-31', 'publishedAt': '2026-03-31',
                                      'basis': 'snapshot-identity-only', 'source': 'https://example.org/teaching.pdf',
                                      'evidence': {'page': 1, 'quote': '300308 Teaching Issuer', 'documentSha256': '0'*64}}]}
    def test_absent_original_stays_unknown(self):
        before = copy.deepcopy(self.spec)
        result = apply_snapshot_mappings(self.spec, self.mapping)
        self.assertIsNone(result['input']['securities']['CN-equity:300308']['issuer'])
        self.assertEqual(self.spec, before)
    def test_future_source_and_period_gap_not_applied(self):
        self.mapping['mappings'][0]['publishedAt'] = '2026-05-01'
        self.assertEqual(apply_snapshot_mappings(self.spec,self.mapping)['mappingDecisions'][0]['status'],'not-applied-period-or-publication-gap')
        self.mapping['mappings'][0]['publishedAt'] = '2026-03-31'
        self.spec['nodes']['fund']['reportDate'] = '2024-12-31'
        self.assertIsNone(apply_snapshot_mappings(self.spec,self.mapping)['input']['securities']['CN-equity:300308']['issuer'])
    def test_identity_conflict_and_lifetime_inference_refused(self):
        self.mapping['mappings'][0]['code'] = '600519'
        with self.assertRaises(ValueError):apply_snapshot_mappings(self.spec,self.mapping)
        self.mapping['mappings'][0]['code'] = '300308'
        self.mapping['mappings'][0]['validUntil'] = '2030-01-01'
        with self.assertRaises(ValueError):apply_snapshot_mappings(self.spec,self.mapping)
