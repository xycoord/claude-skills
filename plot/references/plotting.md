# Plotting Conventions Reference

Detailed conventions for matplotlib figures in research reports. Read this before generating any plots.

## General setup

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Apply at the start of plot generation
plt.rcParams.update({
    'figure.figsize': (8, 5),
    'figure.dpi': 150,
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.constrained_layout.use': True,  # prevents label clipping
})
```

## Colour palette

Use a consistent colour scheme across all plots in a report. Group colours by method category so the reader can instantly distinguish skylines, baselines, and new methods.

Suggested defaults (but adapt if there are many methods or specific project conventions):

```python
COLOURS = {
    'skyline': '#999999',       # grey family for skylines / upper bounds
    'baseline': '#4878CF',      # blue family for baselines
    'new': '#6ACC65',           # green family for new methods
}

# When there are multiple methods in a category, use shades:
SKYLINE_SHADES = ['#999999', '#BBBBBB']
BASELINE_SHADES = ['#4878CF', '#7BA3E0']
NEW_METHOD_SHADES = ['#6ACC65', '#B5E6A3', '#3D8C40']
```

Define the colour mapping once at report generation time and reuse it for every figure. Every method should map to exactly one colour across the entire report.

## Bar charts

Bar charts are the primary tool for comparing methods on a metric.

### Ordering

Bars are ordered left to right as: **skylines → baselines → new methods**. Within each group, order alphabetically or by performance — just be consistent across plots.

### Baseline reference lines

For each baseline, draw a horizontal dashed line at the baseline's value spanning the full plot width. This makes it easy to see whether new methods beat the baseline without scanning back to the baseline bar.

```python
# After creating bars
for baseline_name, baseline_val in baselines.items():
    ax.axhline(y=baseline_val, color=colour_map[baseline_name],
               linestyle='--', linewidth=1, alpha=0.7,
               zorder=1, label=f'{baseline_name} (ref)')
```

The key detail: use `zorder=1` for reference lines so they sit behind the bars (`zorder=2`) and value annotations (`zorder=3`). This prevents lines from crossing over labels or bar faces.

### Meaningful reference values

If the metric has a well-known reference point (e.g. random chance = 0.5 for AUC, majority class rate for accuracy), draw it as a labelled horizontal line:

```python
ax.axhline(y=0.5, color='#CCCCCC', linestyle=':', linewidth=1,
           zorder=0, label='Random chance')
```

Use a neutral colour and the lowest zorder so it doesn't compete visually with the data.

### Axis ranges for bounded metrics

If a metric has meaningful bounds, set the axis limits to reflect them. For example, AUC should span 0 to 1, not be auto-scaled to a narrow range that exaggerates small differences.

```python
if metric_bounded:
    ax.set_ylim(metric_lower_bound, metric_upper_bound)
```

Use judgement: if all values cluster between 0.92 and 0.97, a 0–1 range might obscure real differences. In that case, use the full range but add an inset or note the scale. The goal is honesty — don't let the axis range mislead.

### Value annotations

Annotate each bar with its numeric value. Place the label just above the bar top (or above the error bar if present).

```python
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + offset,
            f'{val:.3f}', ha='center', va='bottom', fontsize=9, zorder=3)
```

Adjust decimal places to what's meaningful for the metric (e.g. 3 decimal places for AUC, 1 for percentage accuracy).

### Error bars

Include error bars when you have variance data (multiple seeds, folds, etc.). Always state what the error bars represent, either in the figure caption or a note below the plot.

```python
ax.bar(x, means, yerr=stds, capsize=4, error_kw={'linewidth': 1},
       color=colours, edgecolor='white', linewidth=0.5, zorder=2)
```

In the report text or figure title, include something like: "Error bars show ±1 standard deviation over 3 random seeds."

### Spines and grid

Remove top and right spines. Add subtle horizontal grid lines for readability.

```python
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.yaxis.grid(True, linestyle='-', alpha=0.2, zorder=0)
ax.set_axisbelow(True)
```

### Titles

Every plot needs a clear, descriptive title that states what is being compared and on what metric. For example: "AUC-ROC on TruthfulQA by method" rather than just "Results".

### Legends

Place legends outside the plot area to avoid obscuring data:

```python
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
```

If there are many methods, a legend below the plot can work better:

```python
ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center',
          ncol=3, borderaxespad=0)
```

### Long method names

If method names are too long for the x-axis, use the abbreviated forms defined in the report's abbreviation legend. Rotate labels only as a last resort — horizontal abbreviated labels are almost always more readable than rotated full names.

```python
ax.set_xticklabels(abbreviated_names)
```

## Heatmaps

For confusion matrices, attention maps, correlation matrices, etc.

```python
import matplotlib.colors as mcolors

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(data, cmap='Blues', aspect='auto')

# Annotate cells with values
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        colour = 'white' if data[i, j] > threshold else 'black'
        ax.text(j, i, f'{data[i, j]:.2f}', ha='center', va='center',
                color=colour, fontsize=9)

fig.colorbar(im, ax=ax, shrink=0.8)
```

Key conventions:
- Annotate every cell with its value (use white text on dark cells, black on light)
- Include a colour bar
- Use a sequential colourmap (Blues, Greens, or viridis) — avoid rainbow
- Label both axes clearly
- For confusion matrices, put true labels on the y-axis and predicted on the x-axis

## Saving figures

```python
fig.savefig('figures/plot_name.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close(fig)
```

Always use `bbox_inches='tight'` to avoid clipping legends and labels. Use a white background for GitHub readability. Close the figure after saving to free memory.

## Checklist before saving any figure

1. Title is descriptive and specific
2. Axes are labelled with units where applicable
3. Baselines are plotted (or their absence is flagged in the report)
4. Bar order is skylines → baselines → new methods
5. Baseline reference lines are behind bars (low zorder)
6. Bounded metrics use appropriate axis range
7. Meaningful reference values are drawn as labelled horizontal lines
8. Values are annotated on bars
9. Error bars are present if variance data exists, with a note on what they represent
10. Colours are consistent with other plots in the report
11. Top and right spines removed (bar charts)
12. Legend is outside the plot area
13. Abbreviations match the report's abbreviation legend
14. DPI is at least 150, figure size at least 8×5 inches
