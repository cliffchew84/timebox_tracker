#!/usr/bin/env python
# coding: utf-8

import tempfile
from datetime import datetime
import pygsheets
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Authenticate into Google Sheets
json_encode = st.secrets['g_cred'].replace("\\\\", "\\").encode('utf-8')

def _google_creds_as_file():
    temp = tempfile.NamedTemporaryFile()
    temp.write(json_encode)
    temp.flush()
    return temp

def pull_data():

    creds_file = _google_creds_as_file()
    gc = pygsheets.authorize(service_account_file=creds_file.name)

    sh = gc.open('Prod_tracker')

    wks = sh.worksheet_by_title("Day")
    dview = wks.get_as_df()

    wks = sh.worksheet_by_title("Week")
    wview = wks.get_as_df()

    wks = sh.worksheet_by_title("Learning")
    lview = wks.get_as_df()

    return dview, wview, lview

dview, wview, lview = pull_data()

# Start of UI
st.title("Tracking My Activities")
st.write("""
    My name is Cliff, and this is my prototype to track my timeboxing efforts, 
    The entire prototype and its workflow, from the Google Calendar and Sheets API 
    calls, data processing to the frontend (what you are seeing now) is written in Python.
    If you are interested, please visit my blog (coming soon). 
    Best viewed on desktop.
""")

extraction_time = "-".join(str(datetime.now()).split(".")[0].split("-")[1:])

# Daily hours spent
col1, col2 = st.beta_columns([1, 5])
col1.subheader('Last updated')

col1.write(extraction_time)
if col1.button('Refresh Data'):
    dview, wview, lview = pull_data()
    extraction_time = "-".join(str(datetime.now()).split(".")[0].split("-")[1:])

col1.subheader('Daily Hours Spent')
weeks = col1.multiselect(
     "Select the weeks",
     tuple(set([str(i) for i in wview.week])))

# Day View
for col in dview.columns.tolist():
    if col in ['week', 'date', 'day']:
        dview[col] = dview[col].astype(str)
    else:
        dview[col] = dview[col].astype(float)

dview['date'] = ["-".join(i.split("-")[1:]) for i in dview['date']]
dview['y'] = "w" + dview['week'] + ' | ' + dview['date'] + " | " + dview['day'] + " "

if weeks:
    final_dview = dview[
        dview.week.isin(weeks)].reset_index(drop=True)
else:
    final_dview = dview.copy()
    
y = final_dview.sort_values('date').y.values
x = ['Rest', 'Health', 'Admin', 'Leisure', 'Learning', 'Production', 'Work']
x_color = {
    'Admin': '#7CB342', 
    'Health': '#009688', 
    'Learning': '#cc1263',
    'Leisure': '#039BE5', 
    'Rest': '#B39DDB', 
    'Work': '#EF6C00',
    'Production': '#616161'
    }

dbar = go.Figure()
for col in x:
    dbar.add_bar(
        y=y, 
        x=final_dview[col].values,
        orientation='h', 
        name=col,
        marker_color=x_color[col],
    )

dbar.update_yaxes(type='category')
dbar.update_xaxes(tick0=0, dtick=4)
dbar.update_layout(
    barmode="stack", 
    hovermode="y unified", 
    height=40 * len(final_dview['date'].unique()),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y = -.12,
        xanchor="left",
        x=.2),
    margin=dict(
        l=10, #left margin
        r=5, #right margin
        b=0, #bottom margin
        t=10  #top margin
    )
)

col2.plotly_chart(dbar, use_container_width=True)

# Learning Table
learning_style = dict()

for col in lview.columns.tolist():
    if col not in ['week', 'day', 'date']:
        lview[col] = lview[col].astype(float)
        learning_style[col] = "{:.4}"
        lview[col] = [str(i).replace('0.0', '.') for i in lview[col]]

lview['date'] = ["-".join(i.split("-")[1:]) for i in lview['date']]

del lview['week']

## Learning Table
st.subheader("Past 14 Day Learnings")
st.dataframe(lview.style.format(learning_style))

## Weekly aggregations
for col in wview.columns.tolist():
    if col in ['week', 'start_week']:
        wview[col] = wview[col].astype(str)
    else:
        wview[col] = wview[col].astype(float)

wview['y'] = "w" + wview['week'] + ' | ' + wview['start_week']

y = wview.sort_values('week').y.values

wbar = go.Figure()
for col in x:
    wbar.add_bar(
        y=y, 
        x=wview[col].values,
        orientation='h', 
        name=col,
        marker_color=x_color[col],
    )

wbar.update_yaxes(type='category')
wbar.update_xaxes(tick0=0, dtick=4)
wbar.update_layout(
    barmode="stack", 
    hovermode="y unified", 
    height=120 * len(wview['week'].unique()),
    title=dict(
        text= "Weekly Hours Spent",
        y=0.9,
        x=0.5,
        xanchor='center',
        yanchor='top'),
    showlegend=False,
    margin=dict(
        l=10, #left margin
        r=10, #right margin
        b=50, #bottom margin
        t=50  #top margin
    )
)

st.plotly_chart(wbar, use_container_width=True)