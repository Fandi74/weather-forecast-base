# Public benchmark data sources

This directory contains processed public weather data, not company measurements or station configuration. LaGuardia Airport is a public NOAA station, deliberately identified so the comparison can be checked independently.

## Forecasts

Source: [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api), processed GFS model, 24/72/168-hour offsets, 2023 and 2024.

Open-Meteo data are provided under [CC BY 4.0](https://open-meteo.com/en/licence). Credit Open-Meteo when redistributing these data or derived results, link the license, and indicate processing. Free API service restrictions are separate from the data license; consult [terms](https://open-meteo.com/en/terms) before fetching data for a different purpose.

Changes: selected one public location and temperature variable, joined UTC valid hours to quality-filtered station reports, required all three offsets on each accepted hour, and extracted a matched-case CSV. This is not native unmodified GFS output or a full original-model-run archive.

## Observations

Source: NOAA NCEI Integrated Surface Database via the [NOAA Open Data Dissemination archive](https://registry.opendata.aws/noaa-isd/). Public airport station: 72503014732, LaGuardia Airport, New York, United States.

The NOAA NODD archive makes the data openly reusable and requests attribution. NOAA endorsement or affiliation is not implied. The observations here are **processed**: only routine FM-15 temperature reports with accepted quality flags are used, tenths Celsius are converted to Celsius, and the nearest report within 15 minutes is associated with a UTC forecast hour. These processed rows are not presented as original unmodified government records.

## Provenance and scope

`provenance.json` records public station metadata, original source URLs, raw file hashes, transformations, exclusion counts and the frozen matched CSV hash. `matched.csv` contains the transformed hourly pairs used for fitting and evaluation. Raw archives are kept in an ignored local cache and are not part of the proposed public package.

Data attribution here does not add a software license to the project. No proprietary inputs are used. See [evaluation protocol](../../docs/REAL_WORLD_EVALUATION.md) for timing, matching, coverage and inference limitations.
