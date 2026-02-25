(function () {
  const gd = document.getElementById("{plot_id}");
  if (!gd) return;
  const DEBUG = false; 
  if (DEBUG) console.log("smartTicks v7 loaded");

  // ------------------------
  // Formatting helpers
  // ------------------------
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const pad2 = (n) => (n < 10 ? "0" : "") + n;
  const fmtMD = (d) => `${months[d.getMonth()]} ${pad2(d.getDate())}`;
  const fmtHM = (d) => `${pad2(d.getHours())}:${pad2(d.getMinutes())}`;

  function parseCssColor(c) {
    if (!c) return null;
    c = c.trim();

    let m = c.match(/^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i);
    if (m) return { r: +m[1], g: +m[2], b: +m[3] };

    m = c.match(/^rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)$/i);
    if (m) return { r: +m[1], g: +m[2], b: +m[3] };

    m = c.match(/^#([0-9a-f]{6})$/i);
    if (m) {
      const x = m[1];
      return {
        r: parseInt(x.slice(0, 2), 16),
        g: parseInt(x.slice(2, 4), 16),
        b: parseInt(x.slice(4, 6), 16),
      };
    }
    return null;
  }

  function luminance01(rgb) {
    return (0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b) / 255;
  }

  function rgba(rgb, a) {
    return `rgba(${rgb.r},${rgb.g},${rgb.b},${a})`;
  }

  function allAxes(prefix) {
    const re = new RegExp("^" + prefix + "(\\d+)?$");
    return Object.keys(gd._fullLayout || {}).filter((k) => re.test(k));
  }

  // ------------------------
  // Streamlit theme -> Plotly
  // ------------------------
  function readStreamlitCssVars() {
    try {
      const root = parent.document.documentElement;
      const s = getComputedStyle(root);
      return {
        bg: s.getPropertyValue("--background-color").trim(),
        text: s.getPropertyValue("--text-color").trim(),
      };
    } catch (e) {
      return { bg: "", text: "" };
    }
  }

  function computeTheme() {
    const v = readStreamlitCssVars();
    const bgRgb = parseCssColor(v.bg);

    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ?? true;
    const isDark = bgRgb ? (luminance01(bgRgb) < 0.5) : prefersDark;

    const textRgb =
      parseCssColor(v.text) ||
      (isDark ? { r: 245, g: 245, b: 245 } : { r: 25, g: 25, b: 25 });

    const gridBase = isDark ? { r: 255, g: 255, b: 255 } : { r: 0, g: 0, b: 0 };

    return {
      isDark,
      text: `rgb(${textRgb.r},${textRgb.g},${textRgb.b})`,
      // no vertical lines, so only y-grid matters; keep it subtle/grey
      grid: rgba(gridBase, isDark ? 0.10 : 0.12),
      axis: rgba(gridBase, isDark ? 0.28 : 0.22),

      // hover background: MORE transparent (smaller alpha)
      hoverBg: isDark ? "rgba(10,10,10,0.8)" : "rgba(255,255,255,0.0.8)",
      hoverBorder: rgba(gridBase, isDark ? 0.25 : 0.20),
    };
  }

  function applyStreamlitStyle() {
    const t = computeTheme();

    const updates = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      "font.color": t.text,

      // hoverlabel style (applies in unified hover too) [web:183][web:258]
      "hoverlabel.bgcolor": t.hoverBg,
      "hoverlabel.bordercolor": t.hoverBorder,
      "hoverlabel.font.color": t.text,
    };

    // X axes: remove vertical gridlines
    for (const ax of allAxes("xaxis")) {
      updates[`${ax}.showgrid`] = false;
      updates[`${ax}.zeroline`] = false;

      updates[`${ax}.tickfont.color`] = t.text;
      updates[`${ax}.title.font.color`] = t.text;

      updates[`${ax}.linecolor`] = t.axis;
      updates[`${ax}.tickcolor`] = t.axis;
    }

    // Y axes: subtle horizontal gridlines
    for (const ax of allAxes("yaxis")) {
      updates[`${ax}.showgrid`] = true;
      updates[`${ax}.gridcolor`] = t.grid;
      updates[`${ax}.zeroline`] = false;

      updates[`${ax}.tickfont.color`] = t.text;
      updates[`${ax}.title.font.color`] = t.text;

      updates[`${ax}.linecolor`] = t.axis;
      updates[`${ax}.tickcolor`] = t.axis;
    }

    Plotly.relayout(gd, updates);
  }

  // ------------------------
  // Smart ticks
  // ------------------------
  function chooseStepHours(spanHours) {
    if (spanHours >= 24 * 5) return 24;
    if (spanHours >= 24 * 2) return 6;
    if (spanHours >= 24) return 3;
    if (spanHours >= 6) return 1;
    return 0.5;
  }

  function startOfDay(ms) {
    const d = new Date(ms);
    d.setHours(0, 0, 0, 0);
    return d.getTime();
  }

  function computeTicks(x0, x1) {
    const spanHours = (x1 - x0) / 36e5;
    const stepHours = chooseStepHours(spanHours);
    const stepMs = stepHours * 36e5;

    const multiDay = (new Date(x0)).toDateString() !== (new Date(x1)).toDateString();
    const tickvals = [];
    const ticktext = [];

    if (stepHours >= 24) {
      let t = startOfDay(x0);
      if (t < x0) t += 24 * 36e5;
      for (; t <= x1 + 1; t += 24 * 36e5) {
        const d = new Date(t);
        tickvals.push(t);
        ticktext.push(fmtMD(d));
      }
      return { tickvals, ticktext };
    }

    let t = startOfDay(x0);
    for (; t <= x1 + 1; t += stepMs) {
      if (t < x0) continue;

      const d = new Date(t);
      const isMidnight = d.getHours() === 0 && d.getMinutes() === 0;

      let label;
      if (!multiDay) {
        label = (tickvals.length === 0) ? `${fmtMD(d)}<br>${fmtHM(d)}` : fmtHM(d);
      } else {
        if (isMidnight) label = fmtMD(d);
        else if (tickvals.length === 0) label = `${fmtMD(d)}<br>${fmtHM(d)}`;
        else label = fmtHM(d);
      }

      tickvals.push(t);
      ticktext.push(label);
    }

    return { tickvals, ticktext };
  }

  function applySmartTicks() {
    const r = gd?._fullLayout?.xaxis?.range;
    if (!r) return;

    if (DEBUG) console.log("applySmartTicks called, _fullLayout.xaxis.range:", r);
    const x0 = new Date(r[0]).getTime();
    const x1 = new Date(r[1]).getTime();
    if (!isFinite(x0) || !isFinite(x1)) return;

    const out = computeTicks(x0, x1);
    const updates = {};

    for (const ax of allAxes("xaxis")) {
      updates[`${ax}.tickmode`] = "array";
      updates[`${ax}.tickvals`] = out.tickvals;
      updates[`${ax}.ticktext`] = out.ticktext;
    }

    gd._smartTicksBusy = true;
    Plotly.relayout(gd, updates).finally(() => { gd._smartTicksBusy = false; });
  }

  // Initial
  applyStreamlitStyle();
  applySmartTicks();

  // Update on zoom/pan
  gd.on("plotly_relayout", (e) => {
      if (gd._smartTicksBusy) return;
      if (DEBUG) console.log("Relayout event keys:", Object.keys(e));

      // Get data bounds from the first x-axis trace
      const firstTrace = gd.data?.find(t => t.x && t.x.length > 0);
      if (!firstTrace) return;
      
      const xMin = new Date(firstTrace.x[0]).getTime();
      const xMax = new Date(firstTrace.x[firstTrace.x.length - 1]).getTime();
      
      const allUpdates = {};
      
      // Check Y-axes constraints
      for (const axis of ['yaxis2', 'yaxis3', 'yaxis4']) {
          if (e[`${axis}.range[0]`] !== undefined && e[`${axis}.range[0]`] < 0) {
              if (DEBUG) console.log(`Clamping ${axis}.range[0] from ${e[`${axis}.range[0]`]} to 0`);
              allUpdates[`${axis}.range[0]`] = 0;
          }
      }
      // Constrain humidity (yaxis4) upper bound to 100%
      if (e["yaxis4.range[1]"] !== undefined && e["yaxis4.range[1]"] > 100) {
          if (DEBUG) console.log(`Clamping yaxis4.range[1] from ${e["yaxis4.range[1]"]} to 100`);
          allUpdates["yaxis4.range[1]"] = 110;
      }

      // Check X-axis constraints
      if (e["xaxis.range[0]"] !== undefined || e["xaxis.range[1]"] !== undefined) {
          const currentLayout = gd._fullLayout.xaxis;
          const r0 = e["xaxis.range[0]"] !== undefined
              ? new Date(e["xaxis.range[0]"]).getTime()
              : new Date(currentLayout.range[0]).getTime();
          const r1 = e["xaxis.range[1]"] !== undefined
              ? new Date(e["xaxis.range[1]"]).getTime()
              : new Date(currentLayout.range[1]).getTime();
          
          const clampedR0 = Math.max(r0, xMin);
          const clampedR1 = Math.min(r1, xMax);
          
          if (clampedR0 !== r0 || clampedR1 !== r1) {
              allUpdates["xaxis.range"] = [new Date(clampedR0), new Date(clampedR1)];
          }
      }
      
      // Apply ALL constraints together if any exist
      if (Object.keys(allUpdates).length > 0) {
          gd._smartTicksBusy = true;
          Plotly.relayout(gd, allUpdates).finally(() => { 
            gd._smartTicksBusy = false; 
            applySmartTicks();
          });
          return;
      }
      
      // Apply smart ticks if range changed
      if (e["xaxis.range[0]"] || e["xaxis.range[1]"] || e["xaxis.range"] ||  e["xaxis.autorange"]) {
          applySmartTicks();
      }
  });

  // Update on theme changes
  const obs = new MutationObserver(() => applyStreamlitStyle());
  obs.observe(parent.document.documentElement, { attributes: true, attributeFilter: ["style", "class"] });
})();
