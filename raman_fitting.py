import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium", app_title="Raman Spectrum Fitting")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from lmfit.models import PseudoVoigtModel
    import pandas as pd
    import io
    import openpyxl  # explicit import for WASM dependency detection

    return PseudoVoigtModel, io, mo, np, pd, plt


@app.cell
def _(mo):
    mo.md("""
    # Raman Spectrum Fitting Tool

    Interactive pseudo-Voigt peak fitting for Raman spectroscopy data.

    1. Upload your spectrum file (two-column `.txt`: wavenumber and intensity)
    2. Adjust the wavenumber range and select bands
    3. An initial fit runs automatically — fine-tune the parameters as needed
    4. Click **Fit** to re-fit with your adjusted parameters
    5. Download results as Excel files
    """)
    return


@app.cell
def _(mo):
    file_upload = mo.ui.file(
        filetypes=[".txt"],
        kind="area",
        label="Drop your Raman spectrum file here or click to browse",
    )
    file_upload
    return (file_upload,)


@app.cell
def _(file_upload, io, mo, np):
    mo.stop(not file_upload.value, mo.md("*Upload a `.txt` spectrum file to begin.*"))
    _contents = file_upload.value[0].contents
    infilename = file_upload.value[0].name
    raw_data = np.loadtxt(io.BytesIO(_contents))
    raw_x = raw_data[:, 0]
    raw_y = raw_data[:, 1]
    mo.md(
        f"**{infilename}** loaded — {len(raw_x)} points, "
        f"{raw_x.min():.0f}–{raw_x.max():.0f} cm-1"
    )
    return infilename, raw_x, raw_y


@app.cell
def _(mo, raw_x):
    _lo = int(raw_x.min())
    _hi = int(raw_x.max())
    range_slider = mo.ui.range_slider(
        start=_lo,
        stop=_hi,
        step=10,
        value=[max(_lo, 1000), min(_hi, 3100)],
        label="**Wavenumber range (cm-1)**",
        full_width=True,
    )
    range_slider
    return (range_slider,)


@app.cell
def _(np, range_slider, raw_x, raw_y):
    xmin, xmax = range_slider.value
    _mask = (raw_x >= xmin) & (raw_x <= xmax)
    x = raw_x[_mask]
    _y_raw = raw_y[_mask]
    y = _y_raw - np.min(np.abs(_y_raw))
    _dx = np.min(np.diff(x))
    y = 100 * y / (np.sum(y) * _dx)
    return x, xmax, xmin, y


@app.cell
def _():
    BANDS = [
        {"name": "G", "prefix": "G_", "center": 1580, "cmin": 1550, "cmax": 1600, "sigma": 40, "smax": 100, "amp": 10, "amax": 100, "fraction": 1.0},
        {"name": "D", "prefix": "D_", "center": 1350, "cmin": 1300, "cmax": 1400, "sigma": 40, "smax": 100, "amp": 10, "amax": 100, "fraction": 1.0},
        {"name": "D'", "prefix": "Dprime_", "center": 1620, "cmin": 1600, "cmax": 1650, "sigma": 40, "smax": 100, "amp": 10, "amax": 100, "fraction": 1.0},
        {"name": "D3", "prefix": "D3_", "center": 1500, "cmin": 1420, "cmax": 1520, "sigma": 40, "smax": 1000, "amp": 10, "amax": 100, "fraction": 0.0},
        {"name": "D4", "prefix": "D4_", "center": 1100, "cmin": 1000, "cmax": 1250, "sigma": 40, "smax": 1000, "amp": 10, "amax": 100, "fraction": 0.0},
        {"name": "2D1", "prefix": "twoD1_", "center": 2680, "cmin": 2600, "cmax": 2750, "sigma": 40, "smax": 1000, "amp": 10, "amax": 100, "fraction": 0.8},
        {"name": "2D2", "prefix": "twoD2_", "center": 2450, "cmin": 2400, "cmax": 2500, "sigma": 40, "smax": 100, "amp": 10, "amax": 100, "fraction": 0.8},
        {"name": "2D3", "prefix": "twoD3_", "center": 2950, "cmin": 2900, "cmax": 3000, "sigma": 40, "smax": 100, "amp": 10, "amax": 100, "fraction": 0.8},
    ]
    return (BANDS,)


@app.cell
def _(BANDS, mo, xmax, xmin):
    _in_range = [b["name"] for b in BANDS if xmin <= b["center"] <= xmax]
    band_selector = mo.ui.multiselect(
        options=[b["name"] for b in BANDS],
        value=_in_range,
        label="**Active bands** (auto-selected by range)",
    )
    band_selector
    return (band_selector,)


@app.cell
def _(mo):
    get_ui_params, set_ui_params = mo.state(None)
    get_fit_result, set_fit_result = mo.state(None)
    return get_fit_result, get_ui_params, set_fit_result, set_ui_params


@app.cell
def _(PseudoVoigtModel):
    def do_fit(x, y, active_bands, params_dict):
        """Build composite model, fit, return (result, extracted_params)."""
        _models = [PseudoVoigtModel(prefix=b["prefix"]) for b in active_bands]
        _composite = _models[0]
        for _m in _models[1:]:
            _composite += _m
        _params = _composite.make_params()
        for _b in active_bands:
            _key = _b["prefix"].rstrip("_")
            _prefix = _b["prefix"]
            _frac = params_dict.get(f"{_key}_fraction", _b["fraction"])
            _params[_prefix + "center"].set(
                params_dict[f"{_key}_center"], min=_b["cmin"], max=_b["cmax"]
            )
            _params[_prefix + "sigma"].set(
                params_dict[f"{_key}_sigma"], min=1, max=_b["smax"]
            )
            _params[_prefix + "amplitude"].set(
                params_dict[f"{_key}_amp"], min=0, max=_b["amax"]
            )
            if _frac == 0.0 or _frac == 1.0:
                _params[_prefix + "fraction"].set(_frac, vary=False)
            else:
                _params[_prefix + "fraction"].set(_frac, min=0, max=1)
        _result = _composite.fit(y, _params, x=x)
        # Extract fitted values into flat dict matching UI keys
        _extracted = {}
        for _b in active_bands:
            _key = _b["prefix"].rstrip("_")
            _prefix = _b["prefix"]
            _extracted[f"{_key}_center"] = _result.params[_prefix + "center"].value
            _extracted[f"{_key}_sigma"] = _result.params[_prefix + "sigma"].value
            _extracted[f"{_key}_amp"] = _result.params[_prefix + "amplitude"].value
            _extracted[f"{_key}_fraction"] = _result.params[_prefix + "fraction"].value
        return _result, _extracted

    return (do_fit,)


@app.cell
def _(BANDS, band_selector, do_fit, set_fit_result, set_ui_params, x, y):
    _active = [b for b in BANDS if b["name"] in band_selector.value]
    _init = {}
    for _b in _active:
        _key = _b["prefix"].rstrip("_")
        _init[f"{_key}_center"] = _b["center"]
        _init[f"{_key}_sigma"] = _b["sigma"]
        _init[f"{_key}_amp"] = float(_b["amp"])
        _init[f"{_key}_fraction"] = _b["fraction"]
    _result, _extracted = do_fit(x, y, _active, _init)
    set_ui_params(_extracted)
    set_fit_result(_result)
    return


@app.cell
def _(BANDS, band_selector, get_ui_params, mo):
    _fitted = get_ui_params()
    mo.stop(_fitted is None)
    _active = [b for b in BANDS if b["name"] in band_selector.value]
    mo.stop(not _active, mo.md("*Select at least one band above.*"))

    _rows = []
    _kwargs = {}
    for _b in _active:
        _key = _b["prefix"].rstrip("_")
        _center = _fitted.get(f"{_key}_center", _b["center"])
        _sigma = _fitted.get(f"{_key}_sigma", _b["sigma"])
        _amp = _fitted.get(f"{_key}_amp", float(_b["amp"]))
        _frac = _fitted.get(f"{_key}_fraction", _b["fraction"])

        _rows.append(
            f"<tr>"
            f"<td><strong>{_b['name']}</strong></td>"
            f"<td>{{{_key}_center}}</td>"
            f"<td>{{{_key}_sigma}}</td>"
            f"<td>{{{_key}_amp}}</td>"
            f"<td>{{{_key}_fraction}}</td>"
            f"</tr>"
        )
        _kwargs[f"{_key}_center"] = mo.ui.number(
            value=_center, start=_b["cmin"], stop=_b["cmax"], step=1, label=""
        )
        _kwargs[f"{_key}_sigma"] = mo.ui.number(
            value=_sigma, start=1, stop=_b["smax"], step=1, label=""
        )
        _kwargs[f"{_key}_amp"] = mo.ui.number(
            value=_amp, start=0.0, stop=float(_b["amax"]), step=0.5, label=""
        )
        _kwargs[f"{_key}_fraction"] = mo.ui.number(
            value=_frac, start=0.0, stop=1.0, step=0.1, label=""
        )

    _template = (
        "<table style='width:100%; border-collapse:collapse;'>"
        "<tr style='border-bottom:2px solid #ccc;'>"
        "<th style='text-align:left; padding:4px;'>Band</th>"
        "<th style='text-align:left; padding:4px;'>Center (cm-1)</th>"
        "<th style='text-align:left; padding:4px;'>Sigma</th>"
        "<th style='text-align:left; padding:4px;'>Amplitude</th>"
        "<th style='text-align:left; padding:4px;'>Fraction (0=G, 1=L)</th>"
        "</tr>"
        + "".join(_rows)
        + "</table>"
    )

    band_ui = mo.ui.batch(mo.md(_template), _kwargs)
    mo.vstack([mo.md("### Peak Parameters"), band_ui])
    return (band_ui,)


@app.cell
def _(band_ui, get_ui_params, mo):
    _current = band_ui.value
    _fitted = get_ui_params()
    _changed = _fitted is not None and _current != _fitted
    mo.md(
        "**Parameters were manually changed.** Click 'Fit Spectrum' to re-fit."
        if _changed else ""
    )
    return


@app.cell
def _(
    BANDS,
    PseudoVoigtModel,
    band_selector,
    band_ui,
    np,
    plt,
    x,
    xmax,
    xmin,
    y,
):
    _vals = band_ui.value
    _active = [b for b in BANDS if b["name"] in band_selector.value]

    _fig, _ax = plt.subplots(figsize=(10, 5))
    _ax.plot(x, y, "o", markersize=2, label="Data", alpha=0.5, color="gray")

    _total = np.zeros_like(x, dtype=float)
    for _b in _active:
        _key = _b["prefix"].rstrip("_")
        _model = PseudoVoigtModel(prefix=_b["prefix"])
        _pars = _model.make_params()
        _pars[_b["prefix"] + "center"].set(_vals[f"{_key}_center"])
        _pars[_b["prefix"] + "sigma"].set(_vals[f"{_key}_sigma"])
        _pars[_b["prefix"] + "amplitude"].set(_vals[f"{_key}_amp"])
        _pars[_b["prefix"] + "fraction"].set(_vals[f"{_key}_fraction"])
        _peak = _model.eval(_pars, x=x)
        _total += _peak
        _ax.fill_between(x, _peak, alpha=0.3, label=_b["name"])

    _ax.plot(x, _total, "r-", lw=1.5, label="Sum", alpha=0.8)
    _ax.plot(x, y - _total - 0.1, "g-", alpha=0.5, label="Residual")
    _ax.set_xlim(xmin, xmax)
    _ax.set_xlabel("Wavenumber (cm$^{-1}$)")
    _ax.set_ylabel("Intensity (a.u.)")
    _ax.legend(loc="upper right")
    _ax.set_title("Spectrum and peaks (updates live)")
    plt.tight_layout()
    _fig
    return


@app.cell
def _(
    BANDS,
    band_selector,
    band_ui,
    do_fit,
    mo,
    set_fit_result,
    set_ui_params,
    x,
    y,
):
    def _on_click(_):
        _active = [b for b in BANDS if b["name"] in band_selector.value]
        _result, _extracted = do_fit(x, y, _active, band_ui.value)
        set_ui_params(_extracted)
        set_fit_result(_result)

    fit_button = mo.ui.button(label="Fit Spectrum", on_click=_on_click)
    mo.hstack(
        [fit_button, mo.md("*Adjust parameters above, then click to re-fit.*")],
        justify="start",
        gap=1,
    )
    return


@app.cell
def _(get_fit_result, infilename, io, mo, np, pd, x, y):
    _result = get_fit_result()
    mo.stop(_result is None)

    # Build result table (parameters +/- stderr)
    _result_dict = {}
    for _key in _result.params:
        _result_dict[_key + "-value"] = _result.params[_key].value
        _result_dict[_key + "-stderr"] = _result.params[_key].stderr

    # G/D ratio if both bands are present
    if "G_amplitude" in _result.params and "D_amplitude" in _result.params:
        _g = _result.params["G_amplitude"]
        _d = _result.params["D_amplitude"]
        _ratio = _g.value / _d.value
        _result_dict["G/D_ratio-value"] = _ratio
        if _g.stderr is not None and _d.stderr is not None:
            _result_dict["G/D_ratio-stderr"] = _ratio * (
                _g.stderr / _g.value + _d.stderr / _d.value
            )
        else:
            _result_dict["G/D_ratio-stderr"] = np.nan

    _tuples = []
    for _key in _result_dict:
        _first, _rest = _key.split("_", 1)
        _param, _stat = _rest.split("-", 1)
        _tuples.append((_first, _param, _stat))

    _index = pd.MultiIndex.from_tuples(_tuples)
    _sr = pd.Series(list(_result_dict.values()), index=_index)
    _df_table = _sr.unstack(level=-1).sort_index(axis=1, ascending=False)

    # Build plot data table
    _comps = _result.eval_components(x=x)
    _df_plot = pd.DataFrame({
        "wavenumber": x,
        "observed": y,
        "fitted": _result.best_fit,
        "residual": y - _result.best_fit,
    })
    for _comp_key in _comps:
        _df_plot[_comp_key.replace("_", "")] = _comps[_comp_key]

    # Generate Excel files in memory
    _buf_table = io.BytesIO()
    _df_table.to_excel(_buf_table, engine="openpyxl")
    _buf_table.seek(0)

    _buf_plot = io.BytesIO()
    _df_plot.to_excel(_buf_plot, engine="openpyxl", index=False)
    _buf_plot.seek(0)

    mo.vstack([
        mo.md(f"### Fit Result (reduced chi-squared = {_result.redchi:.6f})"),
        _df_table,
        mo.md("### Download Results"),
        mo.hstack([
            mo.download(
                _buf_table.getvalue(),
                filename=infilename + "_result_table.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                label="Download Fit Parameters (.xlsx)",
            ),
            mo.download(
                _buf_plot.getvalue(),
                filename=infilename + "_result_plot.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                label="Download Plot Data (.xlsx)",
            ),
        ], justify="start", gap=1),
    ])
    return


if __name__ == "__main__":
    app.run()
