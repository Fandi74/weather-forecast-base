"""Frozen public-data temperature evaluation; no network access during scoring."""
import csv
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import fmean

from src.model import ALPHAS, fit, metrics, predict

ROOT = Path(__file__).resolve().parents[1]
LEADS = (24, 72, 168)
METHODS = ('raw', 'mean_bias', 'ridge')


def load_rows(base=ROOT / 'data/public'):
    path = base / 'matched.csv'
    provenance = json.loads((base / 'provenance.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != provenance['matched_sha256']:
        raise ValueError('Frozen public input hash differs')
    with path.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    seen = set()
    for row in rows:
        for key in ('lead_hours', 'local_hour', 'valid_hour', 'observation_offset_minutes'):
            row[key] = int(row[key])
        for key in ('forecast_temperature', 'observed_temperature'):
            row[key] = float(row[key])
            if not math.isfinite(row[key]):
                raise ValueError('Nonfinite benchmark value')
        valid = datetime.fromisoformat(row['valid_time_utc'])
        cutoff = datetime.fromisoformat(row['cutoff_time_utc'])
        measured = datetime.fromisoformat(row['observation_time_utc'])
        if valid - cutoff != timedelta(hours=row['lead_hours']):
            raise ValueError('Wrong forecast offset')
        if row['quality'] not in ('1', '5') or abs((measured - valid).total_seconds()) > 900:
            raise ValueError('Observation reference violates matching contract')
        key = (row['valid_time_utc'], row['lead_hours'])
        if key in seen or row['lead_hours'] not in LEADS:
            raise ValueError('Duplicate or unexpected forecast case')
        seen.add(key)
    return rows


def partition(rows):
    groups = {
        'train': [r for r in rows if '2023-01-01' <= r['valid_time_utc'] < '2023-09-23'],
        'validation': [r for r in rows if '2023-10-01' <= r['valid_time_utc'] < '2023-12-23'],
        'test': [r for r in rows if '2024-01-01' <= r['valid_time_utc'] < '2025-01-01'],
    }
    for name, records in groups.items():
        if not records:
            raise ValueError('Missing benchmark partition: ' + name)
    for previous, following in [('train', 'validation'), ('validation', 'test')]:
        latest = max(datetime.fromisoformat(r['observation_time_utc']) for r in groups[previous])
        earliest = min(datetime.fromisoformat(r['cutoff_time_utc']) for r in groups[following])
        if latest + timedelta(hours=24) >= earliest:
            raise ValueError('Assumed observation availability crosses later cutoff')
    return groups


def train_real(groups):
    """No test values read: independent per-offset training and validation selection."""
    models = {}
    for lead in LEADS:
        training = [r for r in groups['train'] if r['lead_hours'] == lead]
        validation = [r for r in groups['validation'] if r['lead_hours'] == lead]
        bias = fmean(r['observed_temperature'] - r['forecast_temperature'] for r in training)
        candidates = []
        for alpha in ALPHAS:
            model = fit(training, 'temperature', alpha)
            score = metrics([r['observed_temperature'] for r in validation],
                            [predict(r, 'temperature', 'ridge', {'ridge': model}) for r in validation])
            candidates.append((score['mae'], alpha, model))
        selected = min(candidates, key=lambda c: (c[0], c[1]))
        models[str(lead)] = {'mean_bias': bias, 'ridge': selected[2],
                             'validation_candidates': [{'mae': mae, 'alpha': alpha} for mae, alpha, _ in candidates],
                             'training_count': len(training), 'validation_count': len(validation)}
    return models


def season(month):
    return ('DJF' if month in (12, 1, 2) else 'MAM' if month in (3, 4, 5)
            else 'JJA' if month in (6, 7, 8) else 'SON')


def week_key(timestamp):
    day = datetime.fromisoformat(timestamp).date()
    return (day - timedelta(days=day.weekday())).isoformat()


def paired_intervals(records, repeats=1000, seed=44107):
    """Resample paired UTC Monday-week clusters, retaining actual cluster sizes."""
    grouped = {}
    for row in records:
        block = grouped.setdefault(week_key(row['valid_time_utc']), [0, 0.0, 0.0])
        actual = row['observed_temperature']
        raw_error = abs(row['raw'] - actual)
        block[0] += 1
        block[1] += raw_error - abs(row['mean_bias'] - actual)
        block[2] += raw_error - abs(row['ridge'] - actual)
    blocks = list(grouped.values())
    if len(blocks) < 2:
        return {'weeks': len(blocks), 'raw_minus_mean_bias_mae_ci95': None, 'raw_minus_ridge_mae_ci95': None}
    rng = random.Random(seed)
    samples = [[], []]
    for _ in range(repeats):
        drawn = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        total = sum(b[0] for b in drawn)
        for index in range(2):
            samples[index].append(sum(b[index + 1] for b in drawn) / total)
    def interval(values):
        values.sort()
        def percentile(p):
            location = p * (len(values) - 1)
            lower = int(location)
            upper = min(lower + 1, len(values) - 1)
            return values[lower] + (location - lower) * (values[upper] - values[lower])
        return [percentile(0.025), percentile(0.975)]
    return {'weeks': len(blocks), 'raw_minus_mean_bias_mae_ci95': interval(samples[0]),
            'raw_minus_ridge_mae_ci95': interval(samples[1])}


def summarize(records):
    observed = [r['observed_temperature'] for r in records]
    scores = {method: metrics(observed, [r[method] for r in records]) for method in METHODS}
    return {'cases': len(records), 'distinct_valid_hours': len(set(r['valid_time_utc'] for r in records)),
            'metrics': scores, 'raw_minus_ridge_mae': scores['raw']['mae'] - scores['ridge']['mae'],
            'raw_minus_mean_bias_mae': scores['raw']['mae'] - scores['mean_bias']['mae'],
            **paired_intervals(records)}


def evaluate(rows, models):
    predictions, groups = [], {}
    for row in rows:
        valid = datetime.fromisoformat(row['valid_time_utc'])
        record = {key: row[key] for key in ('valid_time_utc', 'cutoff_time_utc', 'lead_hours',
                                           'observation_time_utc', 'observation_offset_minutes', 'observed_temperature')}
        for method in METHODS:
            record[method] = predict(row, 'temperature', method, models[str(row['lead_hours'])])
        predictions.append(record)
        labels = ['overall', 'lead/' + str(row['lead_hours']), 'month/' + valid.strftime('%Y-%m'),
                  'season/' + season(valid.month), 'quarter/Q' + str((valid.month - 1) // 3 + 1),
                  'lead_season/' + str(row['lead_hours']) + '/' + season(valid.month),
                  'lead_month/' + str(row['lead_hours']) + '/' + valid.strftime('%Y-%m')]
        for label in labels:
            groups.setdefault(label, []).append(record)
    scores = {label: summarize(records) for label, records in sorted(groups.items())}
    return predictions, scores
