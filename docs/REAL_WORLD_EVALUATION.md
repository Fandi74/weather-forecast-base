# Real-world evaluation protocol (local working version)

## Fixed design before inspecting test results

- Public NOAA LaGuardia Airport station 72503014732; not a company station.
- Temperature only. Open-Meteo processed GFS archived fixed-offset forecasts at 24, 72, and 168 hours; NOAA NCEI ISD routine METAR temperature as reference.
- Training: 2023-01-01 through 2023-09-22 UTC. Validation: 2023-10-01 through 2023-12-22 UTC. Requested test window: all of 2024, subject to reported archive availability. The gaps exceed the maximum offset plus a 24-hour assumed observation-availability delay.
- Fit one mean-bias baseline and one ridge correction per lead. Select ridge alpha from 0.1, 1, 10 on validation MAE only. Do not refit on validation or choose a model after inspecting test results.
- Report raw, mean-bias and ridge errors on identical cases. Report months, calendar quarters, Northern Hemisphere meteorological seasons and fixed offsets; publish counts and exclusions.
- Estimate paired MAE differences with fixed calendar-week cluster bootstrap, 1,000 replicates and 95% percentile intervals. Resample the same week for baseline and candidate. Positive raw-minus-candidate difference means lower candidate MAE. These are conditional, retrospective uncertainty estimates, not operational guarantees.

The design was fixed locally before initial test scoring, not externally preregistered. This is a retrospective demonstration, not a prospective forecast trial. A new year or station would be needed to confirm transfer without further analyst selection.

## Observed coverage and result

The common three-offset cohort contains **8,175 of 8,784 requested 2024 hours** (93.1%), from **2024-01-25 12:00 UTC through 2024-12-31 23:00 UTC**, with additional missing hours inside that span. January 1–25 archive gaps are not silently filled. January and DJF therefore have incomplete seasonal coverage. Requiring all offsets on the same valid hour removes some otherwise available shorter-offset cases; the reported lead comparison is conditional on this common cohort.

Across both source years, the preprocessing cascade rejects 40 hours for absent accepted observations and 636 more hours for an incomplete three-offset forecast set. The latter contains 1,668 missing forecast values. These categories are sequential, not independent counts of all source missingness. The frozen dataset contains 50,604 matched rows at three offsets. Scoring partitions contain 19,035 training, 5,964 validation and 24,525 test pairs; embargoed and unused periods are not scored.

The 24-hour MAE changes from 1.261°C to 1.176°C with a paired 95% improvement interval of [0.036, 0.140]°C. For 72 and 168 hours, improvement intervals cross zero. Pooled across offsets, DJF is slightly worse; March and December have negative monthly point improvements. Do not replace these qualifications with a blanket improvement or accuracy claim. Full 72 subgroup scores and available-week counts are in [metrics](../results/real_world/metrics.json); [changing-condition plots](../results/real_world/changing_conditions.png) show the uncertainty.

## Data and timing limitations

Previous Runs is a fixed-offset archive, not a full original-run archive. The derived cutoff timestamp is not an independently verified run release time. Archived forecasts may include provider interpolation and post-processing; call the reference Open-Meteo processed GFS, not raw native GFS.

NOAA measurements are nearest routine FM-15 reports within 15 minutes of the forecast valid hour. Only temperature quality flags 1 or 5 and nonmissing temperatures between -90°C and 60°C are accepted. These are broad QC bounds, not fitted meteorological thresholds. Flags 1/5 indicate passed-all-checks status in the [NOAA ISD format documentation](https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf). Ties prefer the earlier report. Retain signed observation offset and source timestamps. No temporal interpolation or substitution of missing observations is allowed.

The requested airport location is 40.7794°N, 73.8803°W; NOAA metadata place it at about 3 m elevation. The returned processed-model grid point is about 40.8266°N, 73.8281°W with reported grid elevation 24 m. These are intentionally public coordinates. Station/grid representativeness remains a limitation even after requesting the nearest cell and disabling elevation-based adjustment with `elevation=nan`.

NOAA archive observations may have been revised after collection. Actual ingestion times are unavailable; the embargo and assumed delay cannot prove live-system availability. One airport and one test year do not establish cross-location or multi-year seasonal transfer. Meteorological winter in a calendar-year test includes January/February and December, not one contiguous winter.

The week-block intervals account for within-week dependence and paired methods but not all long-range dependence, model training uncertainty, provider changes, observation revision, or multiple subgroup comparisons. Counts of available weeks must accompany intervals. Subgroup results are descriptive and must not trigger retuning on the held-out test.

## Sources and reuse

- [Open-Meteo archive documentation](https://open-meteo.com/en/docs/previous-runs-api); [CC BY 4.0 data attribution and API terms](https://open-meteo.com/en/terms). Use for this independent educational evaluation, not company operations. Data redistribution remains subject to attribution; free API usage and data licensing are distinct.
- [NOAA ISD via NODD](https://registry.opendata.aws/noaa-isd/): public data with attribution requested; no NOAA endorsement is implied. Transformed observations are labeled as processed, not original unmodified NOAA records.
- [NOAA service migration notice](https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly): ISD stopped updating in August 2025, so the test uses a complete historical year rather than presenting incomplete 2025 data as a full seasonal evaluation.

`data/public/provenance.json` records original request URLs, raw-response hashes, transformations, missingness and public station identity. `matched.csv` is a processed, frozen evaluation input. Raw downloads are cached locally and excluded from publication. Public station coordinates in provenance are deliberate and unrelated to company assets.

## Local reproduction

From the repository root:

```sh
# Existing frozen inputs: no network required.
python examples/run_real_world.py --verify
# Regenerate numerical outputs and all three figures.
python examples/run_real_world.py --plots
# Explicit source refresh; needs network and applicable API access.
python examples/fetch_public_data.py
```

Plotting requires the pinned dependencies in `requirements.txt`. Fetching reuses the local ignored cache; remove only the relevant cached source files if intentionally requesting new provider responses. Provider revisions may change the benchmark, so do not overwrite frozen results without recording and reviewing a new provenance version. Verification retrains rather than loading posted weights, checks numerical artifact hashes, and compares models, scores, intervals and timestamped predictions with tolerance 1e-10.
