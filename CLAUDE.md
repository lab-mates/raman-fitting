# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Raman spectroscopy data fitting tool. Loads `.txt` spectra files, normalizes intensity so area = 100, fits 8 Pseudo-Voigt peaks (D, G, D', D3, D4, 2D1, 2D2, 2D3 bands) via non-linear least-squares, and exports results to Excel.

## Running the Analysis

```bash
# Execute notebook and save output
jupyter nbconvert --to notebook --execute raman-fitting.ipynb --output raman-fitting-output.ipynb

# Or launch interactively
jupyter notebook
```

## Dependencies

```bash
pip install numpy matplotlib lmfit pandas openpyxl
```

## Architecture

The entire workflow lives in `raman-fitting.ipynb` (7 cells, sequential):

1. **Imports** — numpy, matplotlib, lmfit.PseudoVoigtModel, pandas
2. **Load & preprocess** — `np.loadtxt()`, filter 800–3100 cm⁻¹, normalize area to 100
3. **Define composite model** — 8 Pseudo-Voigt peaks with initial center/sigma/fraction/amplitude guesses
4. **Fit** — `model.fit(y, params, x=x)` via lmfit
5. **Plot** — data, fit curve, individual peaks, residuals
6. **Export table** — fitted params ± stderr and G/D ratio → `result_table.xlsx`
7. **Export plot data** — wavenumber, observed, fitted, residual, peaks → `result_plot.xlsx`

## Input Data Format

Two-column ASCII `.txt` files (space-separated, CRLF):
```
wavenumber_cm-1    intensity
70                 0
70.5               4.81389E-4
```

Sample files: `Fe.txt`, `Fe2O3.txt`, `FeCl3.txt`, `FeNO3.txt`

## Changing the Input File

Edit **Cell 1** in the notebook:
```python
file = r"Fe2O3.txt"  # change to desired file
```

## Key Scientific Notes

- **Normalization**: intensity scaled so ∫y dx = 100, making results sample-independent
- **G/D ratio**: computed automatically; key disorder metric for graphitic materials
- **Fit quality**: depends heavily on initial parameter guesses in Cell 2; adjust `center`, `sigma`, `fraction`, `amplitude` bounds if fitting fails
- **fraction parameter**: 0 = pure Gaussian, 1 = pure Lorentzian (D and G bands are typically Lorentzian-dominant)
