import copy
import unittest

from examples.fetch_public_data import observations
from src.real_world import load_rows, paired_intervals, partition, train_real


class PublicDataTests(unittest.TestCase):
    def test_observation_filter_and_nearest_tie(self):
        data = ('DATE,REPORT_TYPE,TMP\n'
                '2024-01-01T00:55:00,FM-15,"+0100,1"\n'
                '2024-01-01T01:05:00,FM-15,"+0200,1"\n'
                '2024-01-01T02:00:00,FM-15,"+0300,2"\n'
                '2024-01-01T03:00:00,FM-16,"+0400,1"\n'
                '2024-01-01T04:00:00,FM-15,"+9999,1"\n').encode()
        parsed, _ = observations(data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(next(iter(parsed.values()))['observed_temperature'], 10.0)
        self.assertEqual(next(iter(parsed.values()))['observation_offset_minutes'], -5)

    def test_common_lead_cohort(self):
        rows = load_rows()
        cohorts = [{r['valid_time_utc'] for r in rows if r['lead_hours'] == lead} for lead in (24, 72, 168)]
        self.assertEqual(cohorts[0], cohorts[1])
        self.assertEqual(cohorts[1], cohorts[2])

    def test_real_test_labels_cannot_change_selected_model(self):
        groups = partition(load_rows())
        original = train_real(groups)
        altered = copy.deepcopy(groups)
        for row in altered['test']:
            row['observed_temperature'] += 500
        self.assertEqual(original, train_real(altered))

    def test_partition_rejects_labels_available_after_cutoff(self):
        rows = load_rows()
        groups = partition(rows)
        last = max(groups['train'], key=lambda r: r['observation_time_utc'])
        last['observation_time_utc'] = '2023-10-01T00:00:00+00:00'
        with self.assertRaises(ValueError):
            partition(rows)

    def test_block_bootstrap_preserves_constant_paired_gain(self):
        records = [{'valid_time_utc': f'2024-01-{day:02d}T00:00:00+00:00',
                    'observed_temperature': 0, 'raw': 3, 'mean_bias': 2, 'ridge': 1}
                   for day in (1, 2, 8, 15)]
        score = paired_intervals(records, repeats=100)
        self.assertEqual(score['weeks'], 3)
        self.assertEqual(score['raw_minus_ridge_mae_ci95'], [2, 2])
        self.assertEqual(score['raw_minus_mean_bias_mae_ci95'], [1, 1])
