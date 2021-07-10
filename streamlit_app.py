#!/usr/bin/env python
# coding: utf-8

import os
import tempfile
import pygsheets
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# Authenticate into Google Sheets
json_encode = st.secrets['g_cred'].replace("\\\\", "\\").encode('utf-8')
# json_encode = os.environ['g_cred'].replace("\\\\", "\\").encode('utf-8')

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

def get_current_datetime():
    return "-".join(
        str(datetime.now() + timedelta(hours=8)
        ).split(".")[0].split("-")[1:])

# Start of UI
st.title("Tracking My Activities")
st.write("""
    My name is Cliff, and this is web app to track my timeboxing efforts, 
    The entire app, from the Google Calendar and Sheets API calls, 
    data processing to the Streamlit frontend (what you see here) is written in Python.
    If you are interested, please visit my blog at https://cliffy-gardens.medium.com/, 
    where I will be posting updates about my life experiments, including this!
    This web app is best viewed on the desktop.
""")

dview, wview, lview = pull_data()
extraction_time = get_current_datetime()

# Daily hours spent
col1, col2 = st.beta_columns([1, 5])
col1.subheader('Last updated')

col1.write(extraction_time)
if col1.button('Refresh Data'):
    dview, wview, lview = pull_data()
    extraction_time = get_current_datetime()

col1.subheader('Daily Hours Spent')
weeks = col1.multiselect(
     "Select the weeks",
     tuple(set([str(i) for i in wview.week])))

################################ Day View ################################
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
dbar.add_vline(x=8, line_width=1, line_dash="dash")
dbar.add_vline(x=16, line_width=1, line_dash="dash")
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

################################ Weekly aggregations ################################
for col in wview.columns.tolist():
    if col in ['week', 'start_week']:
        wview[col] = wview[col].astype(str)
    else:
        wview[col] = wview[col].astype(float)

wview['y'] = "w" + wview['week'] + ' | ' + wview['start_week']

if weeks:
    final_wview = wview[
        wview.week.isin(weeks)].reset_index(drop=True)
else:
    final_wview = wview.copy()

y = final_wview.sort_values('week').y.values

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
wbar.add_vline(x=8, line_width=1, line_dash="dash")
wbar.add_vline(x=16, line_width=1, line_dash="dash")
wbar.update_layout(
    barmode="stack", 
    hovermode="y unified",
    height=220,
    showlegend=False,
    margin=dict(
        l=10, #left margin
        r=10, #right margin
        b=0, #bottom margin
        t=0  #top margin
    )
)

st.subheader("Average Weekly Activities")
st.plotly_chart(wbar, use_container_width=True)

################################ Learning Table ################################
learning_style = dict()

for col in lview.columns.tolist():
    if col not in ['week', 'day', 'date']:
        lview[col] = lview[col].astype(float)
        learning_style[col] = "{:.4}"
        lview[col] = [str(i).replace('0.0', '.') for i in lview[col]]

lview['date'] = ["-".join(i.split("-")[1:]) for i in lview['date']]
del lview['week']

st.subheader("Past 14 Day Learnings")

t_views = list()
for cols in lview.columns:
    t_views.append(lview[cols])

ltable = go.Figure(data=[go.Table(
    header=dict(values=list(lview.columns),
                font=dict(color='white'),
                line_color='#009688',
                fill_color='#039BE5',
                align='center'),
    cells=dict(values=t_views,
               line_color='darkslategray',
               fill_color='lightcyan',
               align='center'))
])

ltable.update_layout(
    margin=dict(
        l=10, #left margin
        r=5, #right margin
        b=0, #bottom margin
        t=0  #top margin
    )
)

st.plotly_chart(ltable, use_container_width=True)