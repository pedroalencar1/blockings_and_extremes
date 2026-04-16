"""
Streamlit app to visualize co-occurrence of extreme events and blocking events 

Pedro Alencar
15.04.2026
"""

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

from global_vars import *# DICT_THRESHOLD_MONTH, LIST_WEEK

from functions import plot_event_block2, get_frac_block_monthly, get_metrics_cm


series_blocking_month = pd.read_csv('data/series_blocking_complete_month.csv')
series_blocking_week = pd.read_csv('data/series_blocking_complete_week.csv')

path_to_month = 'data/monthly/'

with open('data/dict_weekly_stats.pkl', 'rb') as f:
    dict_week_stats = pickle.load(f)

st.set_page_config(layout="wide")

# %% app
st.title("Extreme Events & Blocking Co-occurrence")

ctrl_col, plot_col = st.columns([1, 3])

with ctrl_col:
    st.header("Controls")
    
    selected_period = st.selectbox(
        "Aggregation period",
        options=["Monthly", "Weekly"],
    )

    index_options = DICT_INDEX_FILE_WEEK.keys() if selected_period == "Weekly" else DICT_INDEX_FILE_MONTH.keys()
    selected_index = st.selectbox(
        "Climate index",
        options=index_options,
    )

    if selected_period == "Monthly":
        default_threshold = DICT_THRESHOLD_MONTH[DICT_INDEX_FILE_MONTH[selected_index]][0]
        index_threshold = st.number_input(
            f"Index threshold (type: {DICT_THRESHOLD_MONTH[DICT_INDEX_FILE_MONTH[selected_index]][1]})",
            value=float(default_threshold),
        )

    affected_area_threshold = st.slider(
        "Affected area threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
    )
    
    filter_months = st.checkbox("Show only ASO months (Aug–Oct)", value=False)
    
with plot_col:
		
	if selected_period == "Weekly":
		df_blocking = series_blocking_week
  
		df_extreme = dict_week_stats[DICT_INDEX_FILE_WEEK[selected_index]]
  
		df_extreme_filter = df_extreme.copy()
		if filter_months:
			df_extreme_filter['month'] = df_extreme_filter['time'].dt.month
			df_extreme_filter = df_extreme_filter[df_extreme_filter['month'].isin([8,9,10])]
  		
		fig1 = plot_event_block2(event_df = df_extreme_filter, 
								block_df = df_blocking, 
								plot_class = True, 
								area_threshold = affected_area_threshold, 
								file_name = selected_index) 
		fig2 = plot_event_block2(event_df = df_extreme, 
								block_df = df_blocking, 
								plot_class = False, 
								area_threshold = affected_area_threshold, 
								file_name = selected_index)
	

	else:
		df_blocking = series_blocking_month
  
		df_extreme = get_frac_block_monthly(path_to_month, DICT_INDEX_FILE_MONTH[selected_index])
		df_extreme['day'] = 1  # add dummy day for plotting purposes (monthly data)
		df_extreme['time'] = pd.to_datetime(df_extreme[['year', 'month', 'day']])	
  
		df_extreme_filter = df_extreme.copy()
		if filter_months:
			df_extreme_filter['month'] = df_extreme_filter['time'].dt.month
			df_extreme_filter = df_extreme_filter[df_extreme_filter['month'].isin([8,9,10])]
  			
		fig1 = plot_event_block2(event_df = df_extreme_filter, 
								block_df = df_blocking, 
								plot_class = True, 
								area_threshold = affected_area_threshold, 
								file_name = selected_index) 
		fig2 = plot_event_block2(event_df = df_extreme, 
								block_df = df_blocking, 
								plot_class = False, 
								area_threshold = affected_area_threshold, 
								file_name = selected_index)
 
 
	st.plotly_chart(fig1, use_container_width=True)
	st.plotly_chart(fig2, use_container_width=True)

with ctrl_col: # add metrics from confusion matrix 
    if selected_period == "Weekly":
        df_blocking = series_blocking_week
        df_extreme = dict_week_stats[DICT_INDEX_FILE_WEEK[selected_index]]
        
        dict_metrics = get_metrics_cm(df_extreme, df_blocking, affected_area_threshold)
    else:        
        df_blocking = series_blocking_month
        df_extreme = get_frac_block_monthly(path_to_month, selected_index)
        df_extreme['day'] = 1  # add dummy day for plotting purposes (monthly data)
        df_extreme['time'] = pd.to_datetime(df_extreme[['year', 'month', 'day']])	
        
        dict_metrics = get_metrics_cm(df_extreme, df_blocking, affected_area_threshold)

    st.write("Metrics from confusion matrix (ASO):")
    metrics_df = pd.DataFrame(
        [(k, f"{v:.3f}") for k, v in dict_metrics.items()],
        columns=["Metric", "Value"]
    )
    st.table(metrics_df)

# with plot_col:
#     # fig = go.Figure()

#     # # placeholder trace
#     # fig.add_annotation(
#     #     text="Select options on the left to generate the plot",
#     #     xref="paper", yref="paper",
#     #     x=0.5, y=0.5, showarrow=False,
#     #     font=dict(size=16),
#     # )

#     # fig.update_layout(
#     #     height=600,
#     #     margin=dict(l=20, r=20, t=40, b=20),
#     # )


# 	st.write(df_extreme.columns.tolist()) 

#     st.plotly_chart(fig1, use_container_width=True)
