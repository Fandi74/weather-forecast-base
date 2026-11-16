"""Evaluate frozen public inputs offline; --verify recomputes posted numeric results."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.real_world import load_rows, partition, train_real, evaluate
from src.verification import compare


def write_json(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def run(output, plots=False):
    output.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    groups = partition(rows)
    models = train_real(groups)
    write_json(output / 'models.json', models)  # Written before the test is scored.
    predictions, scores = evaluate(groups['test'], models)
    report = {'dataset': 'Public NOAA observations and Open-Meteo processed GFS forecast offsets',
              'target': 'temperature_c', 'test_year': 2024, 'assumed_observation_delay_hours': 24,
              'bootstrap': {'replicates': 1000, 'seed': 44107, 'unit': 'paired UTC Monday-week cluster',
                            'interval': '95% percentile interval of raw minus corrected MAE'},
              'partition_counts': {k: len(v) for k, v in groups.items()}, 'groups': scores}
    write_json(output / 'metrics.json', report)
    with (output / 'predictions.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(predictions[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(predictions)
    write_json(output / 'checksums.json', {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                                         for name in ('models.json', 'metrics.json', 'predictions.csv')})
    if plots:
        from src.real_world_plotting import plot_real
        plot_real(predictions, scores, output)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/real_world')
    parser.add_argument('--plots', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        with tempfile.TemporaryDirectory() as folder:
            reproduced = Path(folder)
            report = run(reproduced)
            for name in ('models.json', 'metrics.json'):
                compare(json.loads((args.output / name).read_text(encoding='utf-8')),
                        json.loads((reproduced / name).read_text(encoding='utf-8')), name)
            from src.verification import verify
            verify(args.output, reproduced)
        print('Verified public-data models, subgroup metrics, bootstrap intervals and paired predictions.')
    else:
        report = run(args.output, args.plots)
        print(json.dumps({k: report['groups'][k] for k in ('overall', 'lead/24', 'lead/72', 'lead/168')}, indent=2))
