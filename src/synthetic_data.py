"""Fictional hourly forecasts and observations; no real station data."""
import math
import random


def generate(seed=83021, count=2160):
    rng = random.Random(seed)
    weather = 0.0
    rows = []
    for index in range(count):
        valid = index + 24
        hour = valid % 24
        phase = 2 * math.pi * hour / 24
        lead = (1, 6, 12, 24)[index % 4]
        weather = 0.85 * weather + rng.gauss(0, 0.4)
        temperature = 24 + 5 * math.sin(phase) + 2 * math.sin(index / 168) + weather
        humidity = 65 - 15 * math.sin(phase) + 2 * weather
        rows.append({
            'hour_index': index, 'issue_hour': valid - lead, 'valid_hour': valid,
            'local_hour': hour, 'lead_hours': lead,
            'forecast_temperature': temperature + 2 + 1.8 * math.cos(phase)
                                    + 0.04 * lead + rng.gauss(0, 0.8),
            'forecast_humidity': min(100, max(0, humidity - 8 + 6 * math.sin(phase)
                                            + 0.1 * lead + rng.gauss(0, 2.4))),
            'observed_temperature': temperature + rng.gauss(0, 0.3),
            'observed_humidity': min(100, max(0, humidity + rng.gauss(0, 1.2))),
        })
    return rows


def split(rows):
    """60/20/20 boundaries with 24 excluded hours before validation and test."""
    first, second = int(len(rows) * 0.6), int(len(rows) * 0.8)
    groups = {'train': rows[:first], 'validation': rows[first + 24:second],
              'test': rows[second + 24:]}
    if any(not group for group in groups.values()):
        raise ValueError('Not enough records for chronological gaps')
    for earlier, later in [('train', 'validation'), ('validation', 'test')]:
        if max(r['valid_hour'] for r in groups[earlier]) >= min(r['issue_hour'] for r in groups[later]):
            raise ValueError('Training or selection labels cross a later issue time')
    return groups
