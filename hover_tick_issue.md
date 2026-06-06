# Plotly Unified Hover: Tick Label vs Hover Label Conflict

## Setup

- Plotly chart with `hovermode: "x unified"`
- Custom tick labels set via `tickmode: "array"` + `tickvals` + `ticktext`
- `hoverformat` set to `"%a %b %d, %H:%M"` on all x-axes (e.g. "Mon Jun 02, 06:00")
- Charts rendered as HTML via `plotly.io.to_html` inside a Streamlit iframe

## Desired behaviour

- **Tick labels:** date at midnight (`"Mon Jun 02"`), time-only at all other ticks (`"06:00"`, `"12:00"`)
- **Hover x-label:** always shows `"Mon Jun 02, 06:00"` format regardless of position

## Observed behaviour

When `tickmode: "array"` with explicit `ticktext` is used, Plotly appears to use the `ticktext` string as the hover x-label when the cursor is exactly at a tick position, **overriding `hoverformat`**. At non-tick positions, `hoverformat` applies correctly.

Result:
- Hovering at `07:00` (non-tick) → `"Mon Jun 02, 07:00"` ✓
- Hovering at `06:00` (tick, `ticktext = "06:00"`) → `"06:00"` ✗

This does **not** affect the 7-day view because all ticks there are full date labels (`"Mon Jun 02"`), so even when ticktext is used for hover it contains the date.

## What was tried

1. **Re-asserting `hoverformat` in every `Plotly.relayout` call** — no effect; Plotly still uses ticktext at tick positions.

2. **Including the date in all non-midnight ticktext** (e.g. `"Mon 06:00"`) — fixes hover consistency but changes tick label appearance, which was not wanted.

3. **`plotly_hover` DOM override** — listening to `plotly_hover` event and overwriting `.hoverlayer .axistext` text content — did not work, likely because the selector does not match the actual DOM element Plotly renders for the unified hover x-label.

## Question

Is there a supported way in Plotly.js / Plotly Python to have:
- `ticktext` control only the **visual axis tick label**
- `hoverformat` (or any other property) control the **unified hover x-label** independently

…without modifying tick label text or switching away from `tickmode: "array"`?

If DOM manipulation is the right path, what is the correct selector for the x-axis label element inside the unified hover tooltip in `hovermode: "x unified"`?

## Environment

- `plotly` Python package (latest)
- Plotly.js loaded via CDN (`include_plotlyjs="cdn"`)
- Rendered inside a Streamlit `components.html` iframe