---
name: apply-allen-brand
description: Apply Allen Institute brand rules to plots, charts, tables, dashboards, infographics, and scientific visuals. Use when visualizing data or updating visuals to match Allen Institute color, typography, layout, icon, slash, or image-treatment conventions.
user-invocable: true
---

# Allen Institute Brand Plots

Source: `Brand Cheat Sheet.pdf`

Sections marked **(derived)** are guidance inferred from the cheat sheet's examples and principles.

## Goal

preserve data meaning/apply visual language/

## Palette

| Group | Token | RGB | Hex | Pantone | CMYK |
| --- | --- | --- | --- | --- | --- |
| base | Black | 0/0/0 | `#000000` | Black | 20/20/20/100 |
| base | White | 255/255/255 | `#FFFFFF` | not listed | 0/0/0/0 |
| base | Allen Institute Page 1 | 243/240/232 | `#F3F0E8` | Cool Gray 1C | 0/0/5/7 |
| base | Allen Institute Page 2 | 222/217/209 | `#DED9D1` | Warm Gray 1C | 0/2/6/13 |
| base | Allen Institute Gray 1 | 170/163/159 | `#AAA39F` | Warm Gray 6C | 34/30/32/9 |
| base | Allen Institute Gray 2 | 115/115/115 | `#737373` | 4287C | 50/40/40/25 |
| primary | Allen Institute Blue | 100/100/255 | `#6464FF` | 213C | 70/60/0/0 |
| primary | Allen Institute Violet | 130/70/255 | `#8246FF` | 266C | 55/80/0/0 |
| accent | Allen Institute Green | 205/235/5 | `#CDEB05` | 389C | 25/0/100/0 |
| accent | Allen Institute Rose | 255/0/255 | `#FF00FF` | 813C | 0/85/0/0 |
| accent | Allen Institute Maroon | 205/15/85 | `#CD0F55` | 7637C | 0/100/45/15 |
| accent | Allen Institute Teal | 0/165/155 | `#00A59B` | 7710C | 100/0/40/0 |
| accent | Allen Institute Orange | 255/110/0 | `#FF6E00` | 1505C | 0/70/100/0 |
| accent | Allen Institute Ochre | 220/150/0 | `#DC9600` | 6005C | 0/32/100/14 |
| accent | Allen Institute Yellow | 255/235/35 | `#FFEB23` | 102C | 0/0/100/0 |

Note: the PDF prints `#8246E1`, which is inconsistent with both its own RGB value and Pantone 266C — treated as a typo in the source document.

**(derived)** Series: `#6464FF, #FF6E00, #00A59B, #FF00FF, #CDEB05,  #CD0F55, #8246FF,  #DC9600, #FFEB23`
**(derived)** Highlights: `#FF6E00, #CDEB05, #FF00FF, #FFEB23, #CD0F55`
**(derived)** Neutrals: background `#FFFFFF/#F3F0E8`; panel `#FFFFFF/#F3F0E8/#DED9D1`; grid `#DED9D1/#AAA39F`; axis `#000000/#737373`; labels `#000000`; muted `#737373`.

base palette is for backgrounds and factual content/primary and accent palettes add flair/primary also used for backgrounds/

## Plot Color (derived)

These recipes are inferred from infographic samples in the cheat sheet, not stated as rules.

- Analytical background: `white` or `page1`; structure: `page2`, `gray1`, or low-opacity `gray2`; text/axes: `black`.
- Main signal: `blue` and `orange`. Accents mark highlights, thresholds, selections, callouts, or secondary series.
- Use strong accents sparingly. Use maroon for adverse/alert meaning.
- Two-series comparison: `teal` + `orange`; brand-forward combo: `blue` + `violet` + `orange`.
- Dark treatment: `black` background, `white` labels, one or two strong accents.
- Primary-field treatment: `blue` or `violet` background, `white` type, accent highlight (the PDF shows a "headline reversed out of gradation for legibility" treatment as precedent).

## Typography

- Use Allen Institute fonts when available. The family ships in roman and italic, in light/medium/bold (plus light-italic, regular-italic, bold-italic), with two editions: text and headline.
- Text edition is for below 24 pt. Do not alter its letter spacing — wider spacing is intentional for legibility.
- Headline edition is for above 24 pt. Letter-space tightly.
- Fallback: `"Allen Institute Text", "Allen Institute", "Helvetica Neue", Arial, sans-serif`.

**(derived)** Type role mapping for plots:
- Title/Subtitle: Bold. Axes/ticks/legends/captions: Regular. Notes: Light/Regular. Callouts: Semibold/Bold or Head-Semibold/Bold.
- Left-align titles and subtitles

**Text case (derived):** use all lowercase where possible, without capitalization of first letter. Proper nouns included. Do **not** rewrite or recase content where doing so would distort meaning, e.g. gene/protein symbols (e.g. `GFAP`, `Pvalb`), units (`mV`, `Hz`), acronyms with established casing (`ACC`, `MOs`). 

## Layout and hierarchy (derived)

Allen-branded scientific figures should feel open, deliberate, and strongly tiered. Color alone is not enough: leave enough white/page space that the reader can tell figure-level framing, subplot titles, axes, legends, and notes apart at a glance.

- Reserve a clear title band above the plotting grid. Put only the figure title, subtitle, and optional dataset path there; never let this band share vertical space with subplot titles.
- Make figure title/subtitle left-aligned and visually dominant. Use roughly 1.4-1.8x the subplot-title size for the figure title; keep the subtitle smaller and gray2.
- Keep subplot titles short, local, and lower in hierarchy than the figure title. Add internal title padding (`pad=10-14` in Matplotlib) so subplot titles do not touch the axes frame or data.
- Use explicit spacing for multi-panel figures. Start with top margin 0.80-0.86, inter-row spacing 0.35-0.55, and inter-column spacing 0.25-0.40; increase these before shrinking type.
- Put legends outside the data area when possible, aligned to the top or right of the plot group. If a legend must sit inside an axis, give it an empty region and no opaque box unless contrast requires it.
- Keep captions/notes below the grid or in a side rail. Do not tuck notes between subplot rows unless they are attached to one specific panel.
- For dashboards and dense tables, create the same hierarchy: page header, section label, local panel title, control/legend text, then annotations. Use separators, whitespace, or page1/page2 bands before adding more color.

## Direct labels over legends (derived)

For multi-panel scientific plots, prefer direct labeling when each panel has a small number of series. This is more renderable than relying on Allen fonts: it removes legend boxes, keeps the composition open, and lets color do useful work without adding another visual block.

- Replace legends with color-matched text near line endpoints, bar ends, or representative marks. Use a neutral label only when color is already carrying a different meaning.
- Place labels in existing whitespace. Keep them at least 4-8 pt away from axis labels, tick labels, subplot titles, and neighboring data; expand limits or margins before crowding the axes.
- Put endpoint labels just beyond the final visible point when the right side is open. If the endpoint is crowded, move the label to the nearest quiet interior whitespace and use a thin gray1 leader line only when necessary.
- Do not put labels in boxes, pills, or opaque legend frames. If a shared legend is unavoidable, keep it unboxed and outside the plot grid.
- Preserve open composition: direct labels should reduce furniture, not create a new annotation cluster.

Matplotlib starter for multi-panel spacing:

```python
fig, axs = plt.subplots(2, 2, figsize=(8, 6))
fig.subplots_adjust(left=0.09, right=0.98, bottom=0.10, top=0.82, hspace=0.45, wspace=0.32)
fig.suptitle("allen institute/cell types", x=0.09, y=0.97, ha="left", fontsize=18, fontweight="bold")
fig.text(0.09, 0.925, "subtitle or cohort context", ha="left", fontsize=10.5, color=ALLEN["gray2"])
for ax, title in zip(axs.flat, panel_titles):
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", pad=12)
```

Matplotlib endpoint labels:

```python
def label_line_end(ax, x, y, text, color, dx=6, dy=0):
    ax.annotate(
        text,
        xy=(x[-1], y[-1]),
        xytext=(dx, dy),
        textcoords="offset points",
        ha="left",
        va="center",
        color=color,
        fontsize=9,
        clip_on=False,
    )

for ax in axs.flat:
    for line in ax.lines:
        label_line_end(ax, line.get_xdata(), line.get_ydata(), line.get_label(), line.get_color())
    legend = ax.get_legend()
    if legend:
        legend.remove()
    ax.margins(x=0.08)
```

## Motifs

- `/` (forward slash) is used as a separator/it can also be used sparingly as a trailing slash for flair, for example on subsection or subplot titles (don't put a space before the slash)
- (derived) never start a line of text with a slash
- (derived) when using forward slashes for flair, it's confusing to also use them in the same context for units or for ratios: instead use `mV per mm` or `3:1`
- **separator for hierarchical dataset/group name components.** dataset, program, or group name separation e.g. `allen institute/brain science/cell types`. Works well with chart titles, dashboard headers, slide section dividers, and figure captions where the dataset itself is the subject. Keep the slash flush against the name (no space) and lowercase the name unless it contains a symbol that requires exact casing.
- **Icon library (supplemental, not in cheat sheet).** When icons are required, source them from https://fonts.google.com/icons. Prefer the Outlined or Rounded styles at consistent weight and optical size, and apply Allen palette tokens for color rather than the default fills.
- Images: people, science, place. Always cropped and positioned dynamically within the frame, with increased contrast. Treat graphically with luminance or colorization for generalized themes.
- **(derived)** Composition: clean dividers, bold hierarchy, dot grids, big numbers, circles, slashes, high-contrast overlays.

## Suggested starter tokens

```python
ALLEN={"black":"#000000","white":"#FFFFFF","page1":"#F3F0E8","page2":"#DED9D1","gray1":"#AAA39F","gray2":"#737373","blue":"#6464FF","orange":"#FF6E00","green":"#CDEB05","rose":"#FF00FF","maroon":"#CD0F55","teal":"#00A59B","violet":"#8246FF","ochre":"#DC9600","yellow":"#FFEB23"}
ALLEN_SERIES=[ALLEN[k] for k in ["blue","orange","teal","violet","green","rose","maroon","ochre","yellow"]]
plt.rcParams.update({"figure.facecolor":ALLEN["white"],"axes.facecolor":ALLEN["white"],"axes.edgecolor":ALLEN["black"],"axes.labelcolor":ALLEN["black"],"xtick.color":ALLEN["gray2"],"ytick.color":ALLEN["gray2"],"grid.color":ALLEN["page2"],"text.color":ALLEN["black"],"axes.prop_cycle":cycler(color=ALLEN_SERIES),"font.family":["Allen Institute Text","Helvetica Neue","Arial","sans-serif"]})
```

```css
:root{--allen-black:#000000;--allen-white:#fff;--allen-page-1:#f3f0e8;--allen-page-2:#ded9d1;--allen-gray-1:#aaa39f;--allen-gray-2:#737373;--allen-blue:#6464ff;--allen-orange:#ff6e00;--allen-green:#cdeb05;--allen-rose:#f0f;--allen-maroon:#cd0f55;--allen-teal:#00a59b;--allen-violet:#8246ff;--allen-ochre:#dc9600;--allen-yellow:#ffeb23}
```
