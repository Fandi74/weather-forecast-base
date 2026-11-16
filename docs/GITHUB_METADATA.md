# GitHub metadata draft

These are proposed repository settings. They have not been applied remotely.

## Description

Hybrid weather bias-correction portfolio with reproducible synthetic and archived-forecast evaluations, paired uncertainty estimates, and offline numerical verification.

## Topics

```text
weather-forecasting
bias-correction
forecast-verification
meteorology
machine-learning
time-series
python
reproducible-research
uncertainty-quantification
github-actions
```

## CI presentation

The local workflow is `.github/workflows/ci.yml`. It uses read-only repository permissions, pinned official actions, and a Python 3.12/3.15 matrix. It runs tests and both numerical verification commands without API keys, data downloads, plotting dependencies, or company assets.

No hosted run has been triggered because this work has not been pushed. After publication, link the actual Actions run and add its live workflow badge. Do not display a static passing badge or claim a hosted success before a real run completes.
