# Raman fitting

Pseudo-Voigt peak fitting of Raman spectra of carbon materials: the D, G, D′,
D3, D4 and second-order 2D bands. The spectrum is normalised to unit area
(∫y dx = 100), fitted by non-linear least squares with
[lmfit](https://lmfit.github.io/lmfit-py/), and the fitted parameters (± standard
errors) and the G/D ratio are exported to Excel.

## Three ways to run it

| File | What it is | How to run |
|------|------------|------------|
| `raman_fitting.html` | Standalone browser tool | Open it in a browser (loads Plotly and SheetJS from a CDN) |
| `raman_fitting.py` | Interactive [marimo](https://marimo.io) app: upload a file, pick the range and peaks, adjust initial guesses, fit | `marimo run raman_fitting.py` |
| `raman-fitting.ipynb` | Jupyter notebook, step by step | `jupyter notebook`, set `file = r"Fe2O3.txt"` in the first cell |

Python dependencies: `pip install numpy matplotlib lmfit pandas openpyxl`
(plus `marimo` for the app).

The notebook writes `result_table.xlsx` (fitted parameters and G/D ratio) and
`result_plot.xlsx` (wavenumber, observed, fitted, residual and individual peaks).

## Input format

Two-column ASCII text (wavenumber in cm⁻¹, intensity), whitespace-separated:

```
70	0
70.5	5.2914E-4
71	0.00104
```

The fit uses the 800–3100 cm⁻¹ range by default.

## Reference spectra

`Fe.txt`, `Fe2O3.txt`, `FeCl3.txt` and `FeNO3.txt` are example spectra to try the tools with.

## Notes

- Fit quality depends on the initial guesses (center, sigma, fraction, amplitude);
  adjust them if a fit fails.
- `fraction` is the Lorentzian share of each pseudo-Voigt: 0 = Gaussian, 1 = Lorentzian.

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2026 MATES Lab, Universidad de Sevilla-CSIC.
