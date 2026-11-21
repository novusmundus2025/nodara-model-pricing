"""Reject unsupported direct quality-equivalence claims in the public catalog."""

import copy
import json
import unittest

from validate_pricing import ROOT, validate_images


class ImageComparisonTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / 'image-pricing.json').read_text())

    def test_current_catalog_has_no_unsupported_claim(self):
        validate_images(self.catalog)
        self.assertTrue(all(not row['quality_comparison']['direct_comparison_allowed']
                            for row in self.catalog['models']))

    def test_unevaluated_cannot_enable_direct_comparison(self):
        self.catalog['models'][0]['quality_comparison']['direct_comparison_allowed'] = True
        with self.assertRaises(AssertionError):
            validate_images(self.catalog)

    def test_verified_label_requires_matched_settings_and_evidence(self):
        row = self.catalog['models'][0]
        row['quality_comparison'].update(status='verified_equivalent',
                                        direct_comparison_allowed=True,
                                        reference_model='reference-model')
        row['quality_comparison']['matched_settings'] = {
            field: {'nodara': value, 'reference': value}
            for field, value in {'operation': row['operation'], 'width': row['width'],
                                 'height': row['height'], 'output_count': 1,
                                 'quality_preset': 'standard'}.items()
        }
        row['quality_comparison']['evaluation'] = {
            field: 'recorded-evidence'
            for field in self.catalog['comparison_policy']['required_evidence']
        }
        row['quality_comparison']['evaluation'].update(
            evaluation_date='2026-11-21', evaluation_results={'passed': True})
        validate_images(self.catalog)
        for field in self.catalog['comparison_policy']['required_evidence']:
            missing = copy.deepcopy(self.catalog)
            del missing['models'][0]['quality_comparison']['evaluation'][field]
            with self.assertRaises((AssertionError, KeyError)):
                validate_images(missing)
        row['quality_comparison']['matched_settings']['width']['reference'] = 1024
        with self.assertRaises(AssertionError):
            validate_images(self.catalog)


if __name__ == '__main__':
    unittest.main()
