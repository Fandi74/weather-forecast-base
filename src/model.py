"""Small ridge correction learner implemented independently with the standard library."""
import math
from statistics import fmean

TARGETS = ('temperature', 'humidity')
ALPHAS = (0.1, 1.0, 10.0)


def features(row, target):
    # No observed value, future observation, or fitted statistic enters here.
    phase = 2 * math.pi * row['local_hour'] / 24
    return [row['forecast_' + target], row['lead_hours'], math.sin(phase), math.cos(phase)]


def solve(matrix, vector):
    """Gaussian elimination with partial pivoting for a small dense system."""
    a = [list(row) + [value] for row, value in zip(matrix, vector)]
    size = len(vector)
    for col in range(size):
        pivot = max(range(col, size), key=lambda row: abs(a[row][col]))
        a[col], a[pivot] = a[pivot], a[col]
        value = a[col][col]
        if abs(value) < 1e-12:
            raise ValueError('Singular regression system')
        a[col] = [v / value for v in a[col]]
        for row in range(size):
            if row != col:
                factor = a[row][col]
                a[row] = [x - factor * y for x, y in zip(a[row], a[col])]
    return [row[-1] for row in a]


def fit(rows, target, alpha):
    x = [features(r, target) for r in rows]
    means = [fmean(col) for col in zip(*x)]
    scales = [math.sqrt(fmean((row[j] - means[j]) ** 2 for row in x)) or 1.0
              for j in range(len(means))]
    design = [[1.0] + [(v - m) / s for v, m, s in zip(row, means, scales)] for row in x]
    residuals = [r['observed_' + target] - r['forecast_' + target] for r in rows]
    width = len(design[0])
    gram = [[sum(row[i] * row[j] for row in design)
             + (alpha if i == j and i > 0 else 0) for j in range(width)] for i in range(width)]
    rhs = [sum(row[i] * residual for row, residual in zip(design, residuals)) for i in range(width)]
    return {'target': target, 'alpha': alpha, 'means': means, 'scales': scales,
            'coefficients': solve(gram, rhs)}


def predict(row, target, method, bundle):
    raw = row['forecast_' + target]
    if method == 'raw':
        value = raw
    elif method == 'mean_bias':
        value = raw + bundle['mean_bias']
    elif method == 'ridge':
        model = bundle['ridge']
        x = [1.0] + [(v - m) / s for v, m, s in zip(features(row, target), model['means'], model['scales'])]
        value = raw + sum(a * b for a, b in zip(x, model['coefficients']))
    else:
        raise ValueError('Unknown prediction method')
    return min(100, max(0, value)) if target == 'humidity' else value


def metrics(observed, predicted):
    if not observed or len(observed) != len(predicted):
        raise ValueError('Metrics require nonempty matched cases')
    errors = [p - a for a, p in zip(observed, predicted)]
    return {'mae': fmean(abs(e) for e in errors),
            'rmse': math.sqrt(fmean(e * e for e in errors)), 'bias': fmean(errors), 'count': len(errors)}


def train(groups):
    """Fit only on train and choose alpha only on validation; test is not read."""
    result = {}
    for target in TARGETS:
        records = groups['train']
        bias = fmean(r['observed_' + target] - r['forecast_' + target] for r in records)
        candidates = []
        for alpha in ALPHAS:
            model = fit(records, target, alpha)
            predictions = [predict(r, target, 'ridge', {'ridge': model}) for r in groups['validation']]
            score = metrics([r['observed_' + target] for r in groups['validation']], predictions)
            candidates.append((score['mae'], alpha, model))
        _, _, winner = min(candidates, key=lambda item: (item[0], item[1]))
        result[target] = {'mean_bias': bias, 'ridge': winner,
                          'validation_candidates': [{'alpha': a, 'mae': m} for m, a, _ in candidates]}
    return result
