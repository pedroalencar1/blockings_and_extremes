
#%% import libraries and datasets
import streamlit as st

import xarray as xr
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pyproj import Transformer

import os
import pickle

from global_vars import DICT_THRESHOLD_MONTH, LIST_WEEK

#%% functions
label_colors = {'N': 'steelblue', 'S': 'tomato', 'E': 'seagreen', 'W': 'mediumpurple'}

def plot_event_block2(event_df, block_df, plot_class = False, area_threshold=0.25, file_name=''):
    
	if plot_class:
		event_df['class'] = np.where(event_df['frac_event_cells'] > area_threshold, 1, np.nan)
        
		fig = go.Figure()
		fig.add_trace(go.Bar(
			x=event_df['time'].dt.date,
			y=event_df['class'],
			name= f'Event covers > {area_threshold*100:.0f}% of Germany',
			marker_color='black',
			marker_line=dict(width=0, color='black'),
			opacity=0.7,
			yaxis='y1'
		))
	else:
		fig = go.Figure()
		fig.add_trace(go.Scatter(
			x=event_df['time'].dt.date,
			y=event_df['frac_event_cells'],
			mode='lines',
			name='Fraction of drought cells',
			line=dict(color='sienna', width = 0.8),
			yaxis='y1'
		))

	for label, color in label_colors.items():
		mask = block_df['closest_center_label'] == label
		subset = block_df[mask]
		fig.add_trace(go.Bar(
			x=subset['time'],
			y=subset['is_blocking'],
			name=f'Blocking ({label})',
			marker_color=color,
			marker_line=dict(width=0, color='white'),
			opacity=0.3,
			yaxis='y2'
		))

	fig.update_layout(
		title=f'Extreme events and blocking events intersecting Germany - {file_name}',
		xaxis=dict(title='Time', range=['1970-01-01', '2025-12-31']),
		yaxis=dict(title='Affected area', color='sienna', range=[0, 1]),
		yaxis2=dict(title='Blocking (1 = yes)', overlaying='y', side='right', range=[0, 1], color='gray'),
		barmode='overlay',
		bargap=0,
		legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.15, yanchor='top'),
		template='simple_white',
		height=500,
		width=1600
	)
 
	return fig

def get_frac_block_monthly(path_to_folder, file_extreme):
    
    path_extreme = os.path.join(path_to_folder, file_extreme)
    # load dataset
    ds = xr.open_dataset(path_extreme)

    # Transformer from EPSG:3035 to WGS84
    transformer = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)

    var_name = list(ds.keys())[0]
    # Apply mask and compute monthly statistics
    event = ds[var_name].values  # shape: (time, lat, lon)
    
    if DICT_THRESHOLD_MONTH[file_extreme][1] == 'bottom':
        event_masked = (event > DICT_THRESHOLD_MONTH[file_extreme][0])*event
    else:
        event_masked = (event < DICT_THRESHOLD_MONTH[file_extreme][0])*event
        
    event_masked[abs(event_masked) > 0] = 1

    # Build coordinate grids (EPSG:3035 easting/northing)
    lon_name = 'easting' if 'easting' in ds.coords else ('x' if 'x' in ds.coords else list(ds.coords)[-1])
    lat_name = 'northing' if 'northing' in ds.coords else ('y' if 'y' in ds.coords else list(ds.coords)[-2])
    easting_grid, northing_grid = np.meshgrid(ds[lon_name].values, ds[lat_name].values)

    rows = []
    for t_idx in range(event_masked.shape[0]):
        layer = event_masked[t_idx]
        valid_mask = ~np.isnan(layer)
        valid = layer[valid_mask]

        n_event = int(valid.sum())
        frac_event = n_event / len(valid) if len(valid) > 0 else np.nan

        # centroid of event area in EPSG:3035 → convert to WGS84
        if n_event > 0:
            mean_easting = float(np.mean(easting_grid[valid_mask]))
            mean_northing = float(np.mean(northing_grid[valid_mask]))
            centroid_lon, centroid_lat = transformer.transform(mean_easting, mean_northing)
        else:
            centroid_lon, centroid_lat = np.nan, np.nan

        rows.append({
            'time': pd.Timestamp(ds['time'].values[t_idx]),
            'n_event_cells': n_event,
            'frac_event_cells': frac_event,
            'centroid_lon': centroid_lon,
            'centroid_lat': centroid_lat
        })

    event_df = pd.DataFrame(rows)
    event_df['year'] = event_df['time'].dt.year
    event_df['month'] = event_df['time'].dt.month
    event_df['day'] = event_df['time'].dt.day

    return event_df

def get_metrics_cm(event_df, block_df, area_threshold):


	# compute correlation between blocking events and drought conditions above threshold 

	# merge df_extreme with series_blocking_complete on date
	event_df = event_df.copy()
	block_df = block_df.copy()
	event_df['time'] = pd.to_datetime(event_df['time'])
	block_df['time'] = pd.to_datetime(block_df['time'])
	merged = event_df.merge(block_df, on='time', how='outer')
	merged['frac_limit'] = (merged['frac_event_cells'] > area_threshold)*1
  
	merged['month'] = merged['time'].dt.month

	merged_filter = merged[merged['month'].isin([8,9,10])]  # focus on summer months

	# compute F1 score and accuracy for predicting blocking events based on drought fraction > threshold%
	from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score	
	f1 = f1_score(merged_filter['is_blocking'], merged_filter['frac_limit'])
	accuracy = accuracy_score(merged_filter['is_blocking'], merged_filter['frac_limit'])
	recall = recall_score(merged_filter['is_blocking'], merged_filter['frac_limit'])
	precision = precision_score(merged_filter['is_blocking'], merged_filter['frac_limit'])

	dict_metrics = {'f1': f1, 'accuracy': accuracy, 'recall': recall, 'precision': precision}
 
	return dict_metrics