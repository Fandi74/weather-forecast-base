"""Recompute posted numerical artifacts without trusting posted model weights."""
import csv
import hashlib
import json
import math


def compare(left, right, path='root'):
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if not math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError('Reproduction mismatch: ' + path)
    elif isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise ValueError('Different fields: ' + path)
        for key in left:
            compare(left[key], right[key], path + '/' + key)
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise ValueError('Different lengths: ' + path)
        for i, (a, b) in enumerate(zip(left, right)):
            compare(a, b, path + '/' + str(i))
    elif left != right:
        raise ValueError('Reproduction mismatch: ' + path)


def verify(reference, regenerated):
    hashes = json.loads((reference / 'checksums.json').read_text(encoding='utf-8'))
    for name in ('models.json', 'metrics.json', 'predictions.csv'):
        if hashlib.sha256((reference / name).read_bytes()).hexdigest() != hashes.get(name):
            raise ValueError('Posted artifact checksum differs: ' + name)
    for name in ('models.json', 'metrics.json'):
        compare(json.loads((reference / name).read_text(encoding='utf-8')),
                json.loads((regenerated / name).read_text(encoding='utf-8')), name)
    def predictions(folder):
        def cell(value):
            try:
                return float(value)
            except ValueError:
                return value  # Public predictions also contain exact UTC timestamps.
        with (folder / 'predictions.csv').open(encoding='utf-8', newline='') as handle:
            return [{key: cell(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    compare(predictions(reference), predictions(regenerated), 'predictions.csv')
