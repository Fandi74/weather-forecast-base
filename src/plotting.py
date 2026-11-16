"""Render synthetic held-out comparisons using matplotlib."""
def plot(predictions, scores, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    colors = {'observed': '#17202a', 'raw': '#e67e22', 'mean_bias': '#8e44ad', 'ridge': '#1674b8'}
    labels = {'observed': 'Synthetic observation', 'raw': 'Raw synthetic forecast',
              'mean_bias': 'Mean-bias correction', 'ridge': 'Ridge correction'}
    sample = predictions[:96]
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, target, unit in zip(axes, ('temperature', 'humidity'), ('Temperature (°C)', 'Humidity (%)')):
        for method in colors:
            ax.plot([r['valid_hour'] - predictions[0]['valid_hour'] for r in sample],
                    [r[target + '_' + method] for r in sample], label=labels[method],
                    color=colors[method], linewidth=1.35, alpha=0.9)
        ax.set_ylabel(unit)
        ax.grid(alpha=0.2)
    axes[0].legend(loc='upper right', ncol=2, fontsize=8)
    axes[-1].set_xlabel('Hours since held-out test start (first 96 hours)')
    fig.suptitle('Independent synthetic demo — held-out predictions\nFictional data; not real-weather validation', fontsize=13)
    fig.tight_layout()
    fig.savefig(output / 'forecast_vs_observation.png', dpi=150, metadata={'Software': 'Independent synthetic demo'})
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, target, unit in zip(axes, ('temperature', 'humidity'), ('°C', 'percentage points')):
        methods = ['raw', 'mean_bias', 'ridge']
        bars = ax.bar(['Raw', 'Mean bias', 'Ridge'], [scores[target][m]['mae'] for m in methods],
                      color=[colors[m] for m in methods])
        ax.bar_label(bars, fmt='%.3f', padding=3)
        ax.set_title(target.title())
        ax.set_ylabel('Test MAE (' + unit + ')')
        ax.set_ylim(0, max(scores[target][m]['mae'] for m in methods) * 1.25)
        ax.grid(axis='y', alpha=0.2)
    fig.suptitle('Synthetic test errors — all held-out cases; lower is better')
    fig.tight_layout()
    fig.savefig(output / 'test_errors.png', dpi=150, metadata={'Software': 'Independent synthetic demo'})
    plt.close(fig)
