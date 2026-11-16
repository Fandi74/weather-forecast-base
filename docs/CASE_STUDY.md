# Research engineering case study

This page describes my work in a company research context. It is an account of engineering experience, not the source of the runnable synthetic model in this repository. Original company code, measurements, model weights, configurations, and unpublished numerical results are not included.

## My engineering contribution

My contribution was to organize the forecasting work as a sequence of testable engineering decisions: establish a baseline, isolate a candidate change, inspect its behavior, and decide where the evidence supports using it.

### What I designed

- **A baseline-and-candidate workflow.** I kept a reference forecast fixed while investigating separate model candidates, so changing the model would not silently change the comparison.
- **Separate treatment of forecast variables.** I scoped humidity and rainfall improvements separately and retained the temperature baseline while investigating those changes.
- **A composition strategy.** I combined selected variable-specific approaches into a common forecast output while keeping unsupported cases on a baseline or fallback path.
- **An observation comparison strategy.** I used nearby sensors as supplementary context and investigated soil wetting as a possible rainfall signal, with explicit attention to irrigation and fertigation ambiguity.

### What I implemented

- Forecast–observation comparison workflows with explicit sensor-reference choices, timestamp alignment, and missing-data handling.
- Candidate training and prediction workflows using tree-based learners and humidity ensemble combinations.
- Composition of humidity and rainfall candidates with the retained temperature baseline.
- Evaluation summaries and overlapping plots of observations, baseline forecasts, and candidate predictions.

These implementations belong to the original research context. They are described here as my engineering experience; their company-owned code, weights, data, and internal artifacts are not part of this repository.

### What I evaluated

I compared baseline and candidate behavior for temperature, humidity, and rainfall separately. I inspected both aggregate errors and overlapping time-series plots to understand systematic bias, forecast timing, and missed events.

For humidity, I investigated whether candidate models or an ensemble improved agreement with the selected observation reference. For rainfall, I examined event detection and amount prediction separately, including whether local and nearby sensor context could help explain wetting patterns.

I also examined the limits of the evidence: observations already inspected during development, assumed observation delays, site-specific coverage, and inconsistent rainfall improvements. I did not treat an inspected diagnostic period as new blind validation or assume that a better score for one target established improvement for every target.

### What I learned

The most useful outcome was a clearer understanding of where apparent model gains can be misleading: reference-sensor choices affect the target, missing arrival timestamps leave availability uncertain, and dry-heavy rainfall accuracy can conceal missed rain. These findings shaped the evaluation and reporting decisions documented in the [methodology](METHODOLOGY.md).

No company-derived scores or unpublished quantitative findings are disclosed in this account.

## Lessons learned

1. **I learned to preserve the comparison before tuning the model.** A fixed baseline, target definition, and shared observation set make a candidate's behavior easier to interpret.
2. **I learned that sensor semantics are part of the model specification.** Choosing a humidity reference or combining temperature readings changes what is being predicted and scored.
3. **I learned to distinguish timestamps from availability.** Measurement times do not resolve when an operational prediction could actually access a reading.
4. **I learned that rain needs more than a headline accuracy score.** Dry-dominated accuracy and ambiguous soil wetting can both give a misleading impression of useful rain detection.
5. **I learned to qualify evidence.** Development plots and inspected diagnostics are useful for investigation, but an unseen evaluation is still needed for stronger performance claims.
6. **I learned to separate engineering experience from publishable assets.** A portfolio can explain my decisions and limitations without reproducing company-owned materials.


## Boundaries of the historical evidence

The work included inspected development observations, assumed observation delays, site-specific model coverage, and experimental rainfall behavior. It does not establish a new blind real-weather benchmark. Sensor wetting was contextual evidence rather than proof of rain, and nearby measurements were not treated as interchangeable ground truth.

The independently written synthetic demo is a separate completed implementation with its own generated data and held-out test. Its results cannot substantiate claims about the company system. A public forecast adapter and external real-weather evaluation are future work.

Company-owned intellectual property remains with its owner. See the [repository overview](../README.md) for current scope and the [methodology](METHODOLOGY.md) for the independent experiment.
