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

The branch is published and the first hosted run passed on Python 3.12 and 3.15: https://github.com/Fandi74/weather-forecast-base/actions/runs/43831431067. The README includes a live branch-specific workflow badge. Repository description and topics remain proposed settings; they have not been applied.
