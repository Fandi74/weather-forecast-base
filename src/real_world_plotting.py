"""Public-data charts; source station identity is public and unrelated to company assets."""
from datetime import datetime, timedelta


def plot_real(predictions, scores, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    colors = {'raw': '#dc7b24', 'mean_bias': '#8854a1', 'ridge': '#1674b8'}
    metadata = {'Software': 'Independent public-weather evaluation'}
    leads = [24, 72, 168]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for index, method in enumerate(colors):
        axes[0].bar([i + (index - 1) * 0.24 for i in range(3)],
                    [scores['lead/' + str(h)]['metrics'][method]['mae'] for h in leads],
                    width=0.24, label=method.replace('_', ' ').title(), color=colors[method])
    axes[0].set_xticks(range(3), [str(h) + ' h' for h in leads])
    axes[0].set_ylabel('Test temperature MAE (°C); lower is better')
    axes[0].set_title(f"Identical {scores['lead/24']['cases']:,} valid hours at each offset")
    axes[0].legend(fontsize=8)
    for index, lead in enumerate(leads):
        score = scores['lead/' + str(lead)]
        value = score['raw_minus_ridge_mae']
        lower, upper = score['raw_minus_ridge_mae_ci95']
        axes[1].errorbar(value, index, xerr=[[value - lower], [upper - value]],
                         fmt='o', color=colors['ridge'], capsize=5)
    axes[1].set_yticks(range(3), [str(h) + ' h' for h in leads])
    axes[1].axvline(0, color='#666666', linestyle='--', linewidth=1)
    axes[1].set_xlabel('Raw MAE − ridge MAE (°C); positive favors ridge')
    axes[1].set_title(f"Paired 95% intervals; {scores['lead/24']['weeks']} UTC week blocks")
    for ax in axes:
        ax.grid(axis='x' if ax is axes[1] else 'y', alpha=0.18)
    fig.suptitle('Real public-data test: LaGuardia Airport, 2024\nOpen-Meteo processed GFS offsets vs processed NOAA observations', fontsize=12)
    fig.text(0.5, 0.01, 'Sources: open-meteo.com (CC BY 4.0) + NOAA NCEI; processed data, no endorsement', ha='center', fontsize=8)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output / 'lead_comparison.png', dpi=150, metadata=metadata)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw={'width_ratios': [1, 1.6]})
    for ax, prefix, labels in [(axes[0], 'season/', ['DJF', 'MAM', 'JJA', 'SON']),
                                (axes[1], 'month/', ['2024-' + str(m).zfill(2) for m in range(1, 13)])]:
        for index, label in enumerate(labels):
            score = scores[prefix + label]
            lower, upper = score['raw_minus_ridge_mae_ci95']
            value = score['raw_minus_ridge_mae']
            ax.hlines(index, lower, upper, color='#777777', linewidth=1.4)
            ax.plot(value, index, 'o', color='#1674b8' if value >= 0 else '#c65535')
        display = [label + ('*' if label in ('DJF', '2024-01') else '')
                   + f" ({scores[prefix + label]['weeks']} wk)" for label in labels]
        ax.set_yticks(range(len(labels)), display, fontsize=9)
        ax.invert_yaxis()
        ax.axvline(0, color='#555555', linestyle='--', linewidth=1)
        ax.set_xlabel('Raw MAE − ridge MAE (°C)')
        ax.grid(axis='x', alpha=0.18)
    axes[0].set_title('Meteorological seasons')
    axes[1].set_title('Monthly test slices')
    fig.suptitle('Changing conditions: pooled 24/72/168-hour cases\nPositive favors ridge; paired 95% week-block intervals; descriptive subgroups', fontsize=12)
    fig.text(0.5, 0.035, '*January starts Jan 25; winter is incomplete. Few-block intervals can be unstable.', ha='center', fontsize=8)
    fig.text(0.5, 0.01, 'Sources: open-meteo.com (CC BY 4.0) + NOAA NCEI; processed data, no endorsement', ha='center', fontsize=8)
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    fig.savefig(output / 'changing_conditions.png', dpi=150, metadata=metadata)
    plt.close(fig)

    records = [r for r in predictions if r['lead_hours'] == 24]
    lookup = {datetime.fromisoformat(r['valid_time_utc']): r for r in records}
    start = min(lookup)
    times = [start + timedelta(hours=h) for h in range(168)]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    for key, color, label in [('observed_temperature', '#17202a', 'NOAA reference (nearest report)'),
                               ('raw', colors['raw'], 'Processed GFS, 24 h offset'),
                               ('ridge', colors['ridge'], 'Ridge correction')]:
        ax.plot(times, [lookup.get(t, {}).get(key, float('nan')) for t in times],
                color=color, linewidth=1.25, label=label)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.set_ylabel('Temperature (°C)')
    ax.set_xlabel('2024 UTC — first seven test days; gaps are not interpolated')
    ax.grid(alpha=0.18)
    ax.legend(fontsize=8)
    ax.set_title('Public LaGuardia observations and archived forecasts\nFixed display window; this chart is not the full-year score')
    fig.text(0.5, 0.01, 'Sources: open-meteo.com (CC BY 4.0) + NOAA NCEI; processed data, no endorsement', ha='center', fontsize=8)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output / 'forecast_vs_observation.png', dpi=150, metadata=metadata)
    plt.close(fig)
