import copy
import tempfile
import unittest
from pathlib import Path

from examples.run_demo import run
from src.model import features, fit, metrics, predict, train
from src.synthetic_data import generate, split
from src.verification import compare, verify


class DemoTests(unittest.TestCase):
    def test_labels_available_before_next_stage(self):
        groups = split(generate())
        for previous, following in [('train', 'validation'), ('validation', 'test')]:
            self.assertLess(max(r['valid_hour'] for r in groups[previous]),
                            min(r['issue_hour'] for r in groups[following]))

    def test_changed_test_labels_do_not_change_selected_model(self):
        groups = split(generate())
        original = train(groups)
        altered = copy.deepcopy(groups)
        for row in altered['test']:
            row['observed_temperature'] = 9999
            row['observed_humidity'] = -9999
        self.assertEqual(original, train(altered))

    def test_features_never_read_observation_labels(self):
        row = generate(count=1)[0]
        expected = features(row, 'temperature')
        del row['observed_temperature']
        del row['observed_humidity']
        self.assertEqual(features(row, 'temperature'), expected)

    def test_validation_distribution_does_not_change_training_scaler(self):
        groups = split(generate())
        original = train(groups)
        altered = copy.deepcopy(groups)
        for row in altered['validation']:
            row['forecast_temperature'] += 10000
            row['forecast_humidity'] -= 10000
        candidate = train(altered)
        for target in ('temperature', 'humidity'):
            self.assertEqual(original[target]['ridge']['means'], candidate[target]['ridge']['means'])
            self.assertEqual(original[target]['ridge']['scales'], candidate[target]['ridge']['scales'])

    def test_constant_residual_can_be_recovered(self):
        records = generate(count=100)
        for row in records:
            row['observed_temperature'] = row['forecast_temperature'] + 3
        model = fit(records, 'temperature', 1)
        row = generate(seed=2, count=1)[0]
        self.assertAlmostEqual(predict(row, 'temperature', 'ridge', {'ridge': model}),
                               row['forecast_temperature'] + 3)

    def test_metrics_reject_mismatched_cases(self):
        with self.assertRaises(ValueError):
            metrics([1, 2], [1])
        self.assertEqual(metrics([1, 3], [2, 1])['mae'], 1.5)

    def test_same_seed_reproduces_numerical_files(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / 'first', Path(directory) / 'second'
            run(first, plots=False)
            run(second, plots=False)
            for filename in ('models.json', 'metrics.json', 'predictions.csv', 'checksums.json'):
                self.assertEqual((first / filename).read_bytes(), (second / filename).read_bytes())
            verify(first, second)
            (first / 'metrics.json').write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError):
                verify(first, second)

    def test_comparison_rejects_changed_scores(self):
        with self.assertRaises(ValueError):
            compare({'mae': 1.0}, {'mae': 2.0})


if __name__ == '__main__':
    unittest.main()
