"""Run from the repository root: python examples/run_demo.py."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.synthetic_data import generate, split
from src.model import TARGETS, metrics, predict, train


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def run(output, seed=83021, plots=True):
    output.mkdir(parents=True, exist_ok=True)
    rows = generate(seed)
    groups = split(rows)
    models = train(groups)  # Frozen before any test score is computed.
    write_json(output / 'models.json', {'origin': 'independently trained on fictional data', 'seed': seed, 'models': models})
    predictions = []
    scores = {}
    for row in groups['test']:
        record = {'valid_hour': row['valid_hour'], 'issue_hour': row['issue_hour']}
        for target in TARGETS:
            record[target + '_observed'] = row['observed_' + target]
            for method in ('raw', 'mean_bias', 'ridge'):
                record[target + '_' + method] = predict(row, target, method, models[target])
        predictions.append(record)
    for target in TARGETS:
        scores[target] = {method: metrics([r[target + '_observed'] for r in predictions],
                                         [r[target + '_' + method] for r in predictions])
                          for method in ('raw', 'mean_bias', 'ridge')}
    report = {'data': 'fully synthetic forecasts and observations; no real station or company data',
              'seed': seed, 'generated_records': len(rows), 'gap_hours': 24,
              'splits': {name: {'count': len(records), 'first_valid_hour': records[0]['valid_hour'],
                                'last_valid_hour': records[-1]['valid_hour']} for name, records in groups.items()},
              'selection': 'minimum validation MAE per target; ties choose lower alpha; no refit on validation',
              'test': scores}
    write_json(output / 'metrics.json', report)
    with (output / 'predictions.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(predictions[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(predictions)
    if plots:
        from src.plotting import plot
        plot(predictions, scores, output)
    # Stable numerical artifacts only; image bytes can vary with rendering libraries.
    write_json(output / 'checksums.json', {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                                         for name in ('models.json', 'metrics.json', 'predictions.csv')})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    parser.add_argument('--seed', type=int, default=83021)
    parser.add_argument('--no-plots', action='store_true', help='Run numerical demo with Python standard library only')
    parser.add_argument('--verify', action='store_true', help='Recompute and verify saved numerical artifacts without changing them')
    args = parser.parse_args()
    if args.verify:
        from src.verification import verify
        with tempfile.TemporaryDirectory() as directory:
            regenerated = Path(directory)
            run(regenerated, args.seed, plots=False)
            verify(args.output, regenerated)
        print('Verified: retrained models, metrics, predictions and posted checksums.')
    else:
        print(json.dumps(run(args.output, args.seed, not args.no_plots), indent=2))
