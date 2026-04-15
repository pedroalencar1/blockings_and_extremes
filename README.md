# Droughts and Blocking Events — Visualization App

Streamlit app to visualize the co-occurrence of extreme climate events and atmospheric blocking events over Germany.

## Structure

```
app.py              # Main Streamlit application
functions.py        # Plotting and data processing functions
global_vars.py      # Constants (index thresholds, index lists)
data/
  series_blocking_complete_month.csv
  series_blocking_complete_week.csv
  dict_weekly_stats.pkl
  monthly/          # Monthly NetCDF rasters (climate indices)
```

## Data

- **Monthly indices**: NetCDF rasters in `data/monthly/`, one file per climate index (E-OBS derived indicators).
- **Weekly indices**: Pre-computed statistics loaded from `data/dict_weekly_stats.pkl`.
- **Blocking series**: CSV files with daily/weekly blocking classification and closest center label (N/S/E/W).

## Usage

```bash
conda activate py312
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Controls

| Control | Description |
|---|---|
| Aggregation period | Monthly or Weekly |
| Climate index | Index file to analyse |
| Index threshold | Threshold value for classifying extreme conditions (monthly only) |
| Affected area threshold | Minimum fraction of Germany affected to count as an event |
| Show only ASO months | Filter to August–October only |

## Author

Pedro Alencar — April 2026
