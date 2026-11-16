"""Explicit network step: fetch public archives and build a frozen temperature benchmark."""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

STATION = '72503014732'  # Public NOAA LaGuardia Airport station; not a company station.
YEARS = (2023, 2024)
LEADS = (24, 72, 168)
PARAMS = {'latitude': 40.7794, 'longitude': -73.8803, 'models': 'gfs_global',
          'timezone': 'UTC', 'elevation': 'nan', 'cell_selection': 'nearest',
          'temperature_unit': 'celsius',
          'hourly': ','.join('temperature_2m_previous_day' + str(h // 24) for h in LEADS)}


def fetch(url, path):
    if not path.exists():
        print('Downloading ' + path.name, flush=True)
        request = urllib.request.Request(url, headers={'User-Agent': 'IndependentForecastEvaluation/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        temporary = path.with_suffix(path.suffix + '.partial')
        temporary.write_bytes(data)
        temporary.replace(path)
    return path.read_bytes()


def observations(data):
    """Routine METAR only, passed-all-checks temperature, within 15 min of UTC hour."""
    matched, counters = {}, {'rows': 0, 'not_routine_metar': 0, 'bad_temperature': 0,
                             'outside_15_minutes': 0, 'duplicate_hour': 0}
    for row in csv.DictReader(io.StringIO(data.decode('utf-8-sig'))):
        counters['rows'] += 1
        if row['REPORT_TYPE'].strip() != 'FM-15':
            counters['not_routine_metar'] += 1
            continue
        value, quality = row['TMP'].split(',')
        value = int(value)
        if quality not in ('1', '5') or value == 9999 or not -900 <= value <= 600:
            counters['bad_temperature'] += 1
            continue
        measured = datetime.fromisoformat(row['DATE']).replace(tzinfo=timezone.utc)
        hour = (measured + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)
        offset = int((measured - hour).total_seconds() / 60)
        if abs(offset) > 15:
            counters['outside_15_minutes'] += 1
            continue
        candidate = {'observed_temperature': value / 10, 'observation_time_utc': measured.isoformat(),
                     'observation_offset_minutes': offset, 'quality': quality}
        if hour in matched:
            counters['duplicate_hour'] += 1
            old = matched[hour]
            if (abs(offset), measured.isoformat()) >= (abs(old['observation_offset_minutes']), old['observation_time_utc']):
                continue
        matched[hour] = candidate
    return matched, counters


def main():
    base = ROOT / 'data/public'
    cache = base / 'cache'
    cache.mkdir(parents=True, exist_ok=True)
    sources, obs, all_forecasts = [], {}, []
    qc = {}
    for year in YEARS:
        url = f'https://noaa-global-hourly-pds.s3.amazonaws.com/{year}/{STATION}.csv'
        path = cache / f'noaa_{year}.csv'
        data = fetch(url, path)
        parsed, qc[str(year)] = observations(data)
        obs.update(parsed)
        first = next(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
        station = {key: first[key] for key in ('STATION', 'NAME', 'LATITUDE', 'LONGITUDE', 'ELEVATION')}
        sources.append({'provider': 'NOAA NCEI ISD via NODD', 'url': url, 'file': path.name,
                        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
        params = {**PARAMS, 'start_date': f'{year}-01-01', 'end_date': f'{year}-12-31'}
        url = 'https://previous-runs-api.open-meteo.com/v1/forecast?' + urllib.parse.urlencode(params)
        path = cache / f'forecast_{year}.json'
        data = fetch(url, path)
        response = json.loads(data)
        if response.get('utc_offset_seconds') != 0:
            raise ValueError('Expected UTC forecast archive')
        for lead in LEADS:
            key = 'temperature_2m_previous_day' + str(lead // 24)
            if response['hourly_units'][key] != '°C':
                raise ValueError('Unexpected temperature units')
            if len(response['hourly'][key]) != len(response['hourly']['time']):
                raise ValueError('Mismatched forecast arrays')
        sources.append({'provider': 'Open-Meteo processed GFS archive', 'url': url, 'file': path.name,
                        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                        'returned_grid': {k: response[k] for k in ('latitude', 'longitude', 'elevation')},
                        'data_license': 'CC BY 4.0'})
        all_forecasts.append(response['hourly'])
    rows, missing = [], {'missing_observation_hours': 0, 'missing_forecast_values': 0,
                         'hours_excluded_incomplete_lead_set': 0}
    epoch = datetime(2023, 1, 1, tzinfo=timezone.utc)
    for hourly in all_forecasts:
        for index, valid_text in enumerate(hourly['time']):
            valid = datetime.fromisoformat(valid_text).replace(tzinfo=timezone.utc)
            if valid not in obs:
                missing['missing_observation_hours'] += 1
                continue
            values = [hourly['temperature_2m_previous_day' + str(lead // 24)][index] for lead in LEADS]
            if any(value is None for value in values):
                missing['missing_forecast_values'] += sum(value is None for value in values)
                missing['hours_excluded_incomplete_lead_set'] += 1
                continue
            for lead in LEADS:
                value = hourly['temperature_2m_previous_day' + str(lead // 24)][index]
                rows.append({'valid_time_utc': valid.isoformat(),
                             'cutoff_time_utc': (valid - timedelta(hours=lead)).isoformat(),
                             'valid_hour': int((valid - epoch).total_seconds() // 3600),
                             'lead_hours': lead, 'local_hour': valid.hour,
                             'forecast_temperature': value, **obs[valid]})
    output = base / 'matched.csv'
    with output.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    coverage = {}
    for year, hourly in zip(YEARS, all_forecasts):
        times = sorted({r['valid_time_utc'] for r in rows if r['valid_time_utc'].startswith(str(year))})
        coverage[str(year)] = {'requested_hours': len(hourly['time']), 'common_matched_hours': len(times),
                               'coverage_fraction': len(times) / len(hourly['time']),
                               'first_accepted_valid_time': times[0], 'last_accepted_valid_time': times[-1]}
    provenance = {'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'sources': sources,
                  'station': station, 'qc': qc, 'missing': missing, 'matched_rows': len(rows),
                  'coverage': coverage,
                  'matched_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'offset_semantics': 'Documented fixed lead offsets, not original run identifiers; cutoff is derived, not a verified release timestamp.',
                  'hour_convention': 'UTC hour, despite generic model feature name local_hour',
                  'transformations': 'Routine FM-15 only; TMP quality 1/5; nearest observation within 15 minutes; tenths Celsius converted to Celsius; exact forecast-valid-hour join.'}
    (base / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'rows': len(rows), 'station': station, 'qc': qc, 'missing': missing}, indent=2))


if __name__ == '__main__':
    main()
