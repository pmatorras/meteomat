(function () {
  const gd = document.getElementById("{plot_id}");
  if (!gd) return;
  const LANG = "{lang}"; //Language for the ticks, python controlled
  const DEBUG = false; 
  if (DEBUG) console.log("smartTicks v7 loaded");

  // ------------------------
  // Formatting helpers
  // ------------------------
  const monthsEN = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const monthsES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
  const daysEN = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  const daysES = ["Dom","Lun","Mar","Mié","Jue","Vie","Sáb"];
  const pad2 = (n) => (n < 10 ? "0" : "") + n;
  const fmtMD = (d) => {
    const days = LANG === "es" ? daysES : daysEN;
    const months_arr = LANG === "es" ? monthsES : monthsEN;
    return `${days[d.getDay()]} ${months_arr[d.getMonth()]} ${pad2(d.getDate())}`;
  };
  const fmtHM = (d) => `${pad2(d.getHours())}:${pad2(d.getMinutes())}`;

  // Short label for narrow screens: "Wed 4" / "Mié 4"
  const fmtShort = (d) => {
    const days = LANG === "es" ? daysES : daysEN;
    return `${days[d.getDay()]} ${d.getDate()}`;
  };
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
      // Try CSS vars on :root first
      const root = parent.document.documentElement;
      const rootS = getComputedStyle(root);
      const rootBg = rootS.getPropertyValue("--background-color").trim();
      const rootText = rootS.getPropertyValue("--text-color").trim();
      if (rootBg) return { bg: rootBg, text: rootText };

      // Streamlit may set CSS vars on stApp rather than :root
      const appEl = parent.document.querySelector('[data-testid="stApp"]');
      if (appEl) {
        const appS = getComputedStyle(appEl);
        const appBg = appS.getPropertyValue("--background-color").trim();
        const appText = appS.getPropertyValue("--text-color").trim();
        if (appBg) return { bg: appBg, text: appText };

        // Last resort: actual computed background (skip transparent)
        const computed = appS.backgroundColor;
        if (computed && computed !== "rgba(0, 0, 0, 0)" && computed !== "transparent") {
          return { bg: computed, text: appS.color };
        }
      }
    } catch (e) {}
    return { bg: "", text: "" };
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
      axis: rgba(gridBase, isDark ? 0.28 : 0.62),

      // hover background: MORE transparent (smaller alpha)
      hoverBg: isDark ? "rgba(10,10,10,0.8)" : "rgba(255,255,255,0.8)",
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

    // Disable drag-to-zoom on narrow screens (phones) to allow page scrolling
    if (gd.offsetWidth < 430) {
      updates["dragmode"] = false;
    }

    // Subplot titles are annotations — apply text colour explicitly
    const annotations = gd._fullLayout?.annotations || [];
    annotations.forEach((_, i) => {
      updates[`annotations[${i}].font.color`] = t.text;
    });

    Plotly.relayout(gd, updates);
  }

  // ------------------------
  // Smart ticks
  // ------------------------
  function chooseStepHours(spanHours, isNarrow) {
    if (spanHours >= 24 * 5) return 24;
    if (spanHours >= 24 * 2) return isNarrow ? 6 : 12;
    if (spanHours >= 24) return isNarrow ? 3 : 2;
    if (spanHours >= 6) return 1;
    return 0.5;
  }

  function startOfDay(ms) {
    const d = new Date(ms);
    d.setHours(0, 0, 0, 0);
    return d.getTime();
  }

  function computeTicks(x0, x1, isNarrow) {
    const spanHours = (x1 - x0) / 36e5;
    const stepHours = chooseStepHours(spanHours, isNarrow);
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
        // Use fmtShort if narrow
        ticktext.push(isNarrow ? fmtShort(d) : fmtMD(d));
      }
      return { tickvals, ticktext };
    }

    let t = startOfDay(x0);
    for (; t <= x1 + 1; t += stepMs) {
      if (t < x0) continue;

      const d = new Date(t);
      const isMidnight = d.getHours() === 0 && d.getMinutes() === 0;

      let label;
      // Define dateLabel based on screen width
      const dateLabel = isNarrow ? fmtShort(d) : fmtMD(d);
      
      if (!multiDay) {
        label = (tickvals.length === 0) ? `${dateLabel}<br>${fmtHM(d)}` : fmtHM(d);
      } else {
        if (isMidnight) label = dateLabel;
        else if (tickvals.length === 0) label = `${dateLabel}<br>${fmtHM(d)}`;
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

    // check if plot is narrow (e.g. mobile)
    const isNarrow = gd.offsetWidth < 430;

    // pass isNarrow to computeTicks
    const out = computeTicks(x0, x1, isNarrow);
    const updates = {};

    const hoverFmt = LANG === "es" ? "%a %b %d, %H:%M" : "%a %b %d, %H:%M";
    for (const ax of allAxes("xaxis")) {
      updates[`${ax}.tickmode`] = "array";
      updates[`${ax}.tickvals`] = out.tickvals;
      updates[`${ax}.ticktext`] = out.ticktext;
      updates[`${ax}.hoverformat`] = hoverFmt;
    }

    gd._smartTicksBusy = true;
    Plotly.relayout(gd, updates).finally(() => { gd._smartTicksBusy = false; });
  }

  // Initialize — but defer full setup until the chart is actually visible,
  // because charts in inactive tabs have zero dimensions on first load.
  function applyLocale() {
    if (LANG !== "es") return;
    Plotly.register({
      moduleType: "locale",
      name: "es",
      dictionary: {},
      format: {
        days: ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"],
        shortDays: daysES,
        months: ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"],
        shortMonths: monthsES,
      }
    });
    Plotly.relayout(gd, { locale: "es" });
  }

  function fullSetup() {
    applyLocale();
    applyStreamlitStyle();
    applySmartTicks();
  }

  if (gd.offsetWidth > 0) {
    fullSetup();
  } else if (typeof IntersectionObserver !== "undefined") {
    const io = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        io.disconnect();
        const p = Plotly.Plots.resize(gd);
        (p instanceof Promise ? p : Promise.resolve()).then(() => fullSetup());
      }
    }, { threshold: 0.1 });
    io.observe(gd);
  } else {
    fullSetup();
  }

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
      // Temperature (yaxis)
      if (e["yaxis.range[1]"] !== undefined && e["yaxis.range[1]"] > 60) {
          allUpdates["yaxis.range[1]"] = 60; // Max 60°C
      }
      if (e["yaxis.range[0]"] !== undefined && e["yaxis.range[0]"] < -60) {
          allUpdates["yaxis.range[0]"] = -60; // Min -40°C
      }

      // Rainfall (yaxis2)
      if (e["yaxis2.range[0]"] !== undefined && e["yaxis2.range[0]"] < 0) {
          allUpdates["yaxis2.range[0]"] = 0; // Min 0
      }
      if (e["yaxis2.range[1]"] !== undefined && e["yaxis2.range[1]"] > 10) { // Note: 10 in sqrt scale is 100 mm/h
          allUpdates["yaxis2.range[1]"] = 10;
      }

      // Wind (yaxis3)
      if (e["yaxis3.range[0]"] !== undefined && e["yaxis3.range[0]"] < 0) {
          allUpdates["yaxis3.range[0]"] = 0; // Min 0
      }
      if (e["yaxis3.range[1]"] !== undefined && e["yaxis3.range[1]"] > 250) {
          allUpdates["yaxis3.range[1]"] = 250; // Max 250 km/h
      }

      // Constrain humidity (yaxis4) upper bound to 100%
      if (e["yaxis4.range[0]"] !== undefined && e["yaxis4.range[0]"] < 0) {
          allUpdates["yaxis4.range[0]"] = 0; // Min 0
      }

      if (e["yaxis4.range[1]"] !== undefined && e["yaxis4.range[1]"] > 102) {
          if (DEBUG) console.log(`Clamping yaxis4.range[1] from ${e["yaxis4.range[1]"]} to 100`);
          allUpdates["yaxis4.range[1]"] = 110;
      }

      // Check X-axis constraints
      if (e["xaxis.autorange"]) {
          // Autoscale button: override Plotly's padded autorange with exact data bounds.
          // Include ticks in the same relayout so the label at the range edge is not clipped.
          // Also set autorange=false so Plotly doesn't re-apply its own padded range afterward.
          const isNarrow = gd.offsetWidth < 430;
          const out = computeTicks(xMin, xMax, isNarrow);
          allUpdates["xaxis.autorange"] = false;
          allUpdates["xaxis.range"] = [new Date(xMin), new Date(xMax)];
          for (const ax of allAxes("xaxis")) {
              allUpdates[`${ax}.tickmode`] = "array";
              allUpdates[`${ax}.tickvals`] = out.tickvals;
              allUpdates[`${ax}.ticktext`] = out.ticktext;
          }
      } else if (e["xaxis.range[0]"] !== undefined || e["xaxis.range[1]"] !== undefined) {
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
          const ticksIncluded = "xaxis.tickvals" in allUpdates;
          Plotly.relayout(gd, allUpdates).finally(() => {
            gd._smartTicksBusy = false;
            if (!ticksIncluded) applySmartTicks();
          });
          return;
      }
      
      // Apply smart ticks if range changed
      if (e["xaxis.range[0]"] || e["xaxis.range[1]"] || e["xaxis.range"] ||  e["xaxis.autorange"]) {
          applySmartTicks();
      }
  });

  // Override hover x-label to always show full date, independent of tick label text
  gd.on("plotly_hover", function(data) {
    const xVal = data.xvals?.[0] ?? data.points?.[0]?.x;
    if (!xVal) return;
    const d = new Date(xVal);
    if (!isFinite(d.getTime())) return;
    const days_arr = LANG === "es" ? daysES : daysEN;
    const months_arr = LANG === "es" ? monthsES : monthsEN;
    const label = `${days_arr[d.getDay()]} ${months_arr[d.getMonth()]} ${pad2(d.getDate())}, ${fmtHM(d)}`;
    gd.querySelectorAll(".hoverlayer .axistext").forEach(el => { el.textContent = label; });
  });

  // Update on theme changes — watch both root attribute changes and head <style> injections
  const obs = new MutationObserver(() => {
    applyStreamlitStyle();
    if (gd.offsetWidth > 0) applySmartTicks();
  });
  obs.observe(parent.document.documentElement, { attributes: true, attributeFilter: ["style", "class"] });
  try {
    // Streamlit changes theme by injecting/updating <style> in <head>
    obs.observe(parent.document.head, { childList: true });
  } catch (e) {}
})();