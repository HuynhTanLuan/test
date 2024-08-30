# -*- coding: utf-8 -*-
"""
Created on Fri Aug 30 15:14:44 2024

@author: tanluanh
"""

import plotly.graph_objects as go
import plotly.io as pio
#import pandas as pd
pio.renderers.default='browser'
from dash import dcc, html
from dash.dependencies import Input, Output
import dash

import os
if not os.path.exists('report'):
    os.makedirs('report')

#%% Download data from Mongodb
from inphi_datamanagement.spark_mongo_connector import spark_mongo_connector as sm
cn=sm(database='Nova1_B0',bypass=True)
cn.start_connection()  
list_ID=['Id66ccb32d446a7ce6c284ac29S551aed79f5b6','Id66bf324fbddaa6062a2bc43fSf453f8be5c9a','Id66a7734456b7417c66d4e1e1S10a0e5585b60','Id66b9f937e6e38f56e0f4e34aS076f5035f50d','Id66aaadee4a54e3c198d70a2aS5ef391ff6289','Id66a2253240ad25f87e9e81d7S06cca77ab210','Id66aa6de84a54e3c198d709e3S200ec01199f3','Id66b11f722bbe3a0f9f442d22Sf8b05c6bcb01','Id66a22e2040ad25f87e9e81fbSd07d9761094e','Id66ccf1c4446a7ce6c284ac70S9720651b2c25','Id66cbf3ce446a7ce6c284ab54See191d10c867','Id66bef424bddaa6062a2bc3f8S9a75125489b3','Id66beb444bddaa6062a2bc3b1S67b89fbe4c3a','Id66a734c356b7417c66d4e19aS20a99331a028','Id66cc33d7446a7ce6c284ab9bS173316729dee','Id66cc72f2446a7ce6c284abe2Sa96697853ee4','Id66bbbcaabbeda80510aae74cSd22a557c707a','Id66b3683ecf4794bab8d347c1S29ec17f95ea8','Id66b290da2f6542ea0133904eSf3caad3387b9']
query_ID = []
for ID in list_ID:query_ID.append({'_id':{'$eq':ID}})
query_str={"$match":{'$or':query_ID}}
df = cn.read_data_and_export_to_pandas(query=query_str)
cn.stop_connection(hard_stop=True)

#%% Plot pulse response

#Create a Dash application
app = dash.Dash(__name__)


# List of unique values from a DataFrame
def get_unique_values(df):
    dut_list = sorted(df['main_loop_chip_corner'].unique())
    lane_list = sorted(df['main_loop_test_lane'].unique())
    case_vt = sorted(df['main_loop_VT_corners_label'].unique())
    case_duty = sorted(df['DutyCycle'].dropna().unique())
#   case_duty = sorted([round(duty, 2) for duty in df['DutyCycle'].unique() if isinstance(duty, (int, float))])
    return dut_list, lane_list, case_vt, case_duty


# Create the layout of the Dash application
app.layout = html.Div([
    html.H1("Pulse Response Plot"),
    
    html.Div([
        html.Label("DUT"),
        dcc.Dropdown(
            id='dropdown-dut',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': dut, 'value': dut} for dut in get_unique_values(df)[0]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    html.Div([
        html.Label("Lane"),
        dcc.Dropdown(
            id='dropdown-lane',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': f'LTX{lane}', 'value': lane} for lane in get_unique_values(df)[1]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    html.Div([
        html.Label("VT"),
        dcc.Dropdown(
            id='dropdown-vt',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': vt, 'value': vt} for vt in get_unique_values(df)[2]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    html.Div([
        html.Label("Duty Cycle"),
        dcc.Dropdown(
            id='dropdown-duty',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': str(duty), 'value': duty} for duty in get_unique_values(df)[3]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    dcc.Graph(id='graph',
    style={'height': '76vh', 'width': '100%'}
    )
])

# Callback to update the graph based on user selection
@app.callback(
    Output('graph', 'figure'),
    [Input('dropdown-dut', 'value'),
     Input('dropdown-lane', 'value'),
     Input('dropdown-vt', 'value'),
     Input('dropdown-duty', 'value')]
)
def update_graph(selected_dut, selected_lane, selected_vt, selected_duty):
    fig = go.Figure()

    # Filter data based on user selection
    df_filtered = df.copy()
    if selected_dut and selected_dut != 'All':
        df_filtered = df_filtered[df_filtered['main_loop_chip_corner'] == selected_dut]
    if selected_lane and selected_lane != 'All':
        df_filtered = df_filtered[df_filtered['main_loop_test_lane'] == selected_lane]
    if selected_vt and selected_vt != 'All':
        df_filtered = df_filtered[df_filtered['main_loop_VT_corners_label'] == selected_vt]
    if selected_duty and selected_duty != 'All':
        df_filtered = df_filtered[df_filtered['DutyCycle'].round(2) == selected_duty]

    # Add traces to the figure
    for dut in df_filtered['main_loop_chip_corner'].unique():
        dut_df = df_filtered[df_filtered['main_loop_chip_corner'] == dut]
        for lane in df_filtered['main_loop_test_lane'].unique():
            lane_df = dut_df[dut_df['main_loop_test_lane'] == lane]
            for vt in df_filtered['main_loop_VT_corners_label'].unique():
                vt_df = lane_df[lane_df['main_loop_VT_corners_label'] == vt].reset_index().dropna()
                for i in range(len(vt_df['DutyCycle'])):
                    duty = round(vt_df['DutyCycle'][i], 2)
                    name = f'{dut}_LTX{lane}_{vt}_Duty={duty}'
                    fig.add_trace(go.Scatter(y=vt_df.PR_Amp_V[i], mode='lines', name=name))

    fig.update_layout(
        xaxis_title='Sample',
        yaxis_title='Amplitude (V)'
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
#http://127.0.0.1:8050/
    
    
'''    
    
#%% Frequency Response   
    
app = dash.Dash(__name__)
server = app.server
def get_unique_values(df):
    dut_list = sorted(df['main_loop_chip_corner'].unique())
    lane_list = sorted(df['main_loop_test_lane'].unique())
    case_vt = sorted(df['main_loop_VT_corners_label'].unique())
    case_duty = sorted(df['DutyCycle'].dropna().unique())
    return dut_list, lane_list, case_vt, case_duty

app.layout = html.Div([
    html.H1("Frequency Response Plot"),
    
    html.Div([
        html.Label("DUT"),
        dcc.Dropdown(
            id='dropdown-dut',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': dut, 'value': dut} for dut in get_unique_values(df)[0]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    html.Div([
        html.Label("Lane"),
        dcc.Dropdown(
            id='dropdown-lane',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': f'LTX{lane}', 'value': lane} for lane in get_unique_values(df)[1]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    html.Div([
        html.Label("VT"),
        dcc.Dropdown(
            id='dropdown-vt',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': vt, 'value': vt} for vt in get_unique_values(df)[2]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    html.Div([
        html.Label("Duty Cycle"),
        dcc.Dropdown(
            id='dropdown-duty',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': str(duty), 'value': duty} for duty in get_unique_values(df)[3]],
            value='All'
        )
    ],
        style={'margin-bottom': '5px'}),
    
    dcc.Graph(id='graph',
    style={'height': '76vh', 'width': '100%'}
    )
])

@app.callback(
    Output('graph', 'figure'),
    [Input('dropdown-dut', 'value'),
     Input('dropdown-lane', 'value'),
     Input('dropdown-vt', 'value'),
     Input('dropdown-duty', 'value')]
)
def update_graph(selected_dut, selected_lane, selected_vt, selected_duty):
    fig = go.Figure()

    df_filtered = df.copy()
    if selected_dut and selected_dut != 'All':
        df_filtered = df_filtered[df_filtered['main_loop_chip_corner'] == selected_dut]
    if selected_lane and selected_lane != 'All':
        df_filtered = df_filtered[df_filtered['main_loop_test_lane'] == selected_lane]
    if selected_vt and selected_vt != 'All':
        df_filtered = df_filtered[df_filtered['main_loop_VT_corners_label'] == selected_vt]
    if selected_duty and selected_duty != 'All':
        df_filtered = df_filtered[df_filtered['DutyCycle'].round(2) == selected_duty]

    for dut in df_filtered['main_loop_chip_corner'].unique():
        dut_df = df_filtered[df_filtered['main_loop_chip_corner'] == dut]
        for lane in df_filtered['main_loop_test_lane'].unique():
            lane_df = dut_df[dut_df['main_loop_test_lane'] == lane]
            for vt in df_filtered['main_loop_VT_corners_label'].unique():
                vdf = lane_df[lane_df['main_loop_VT_corners_label'] == vt].reset_index().dropna()
                for i in range(len(vdf['DutyCycle'])):
                    duty = round(vdf['DutyCycle'][i], 2)
                    name = f'{dut}_LTX{lane}_{vt}_Duty={duty}'
                    fig.add_trace(go.Scatter(x=[i/1e9 for i in vdf.FR_fHz[i]],y=vdf.FR_BW3dB[i], mode='lines',name=name+"_BW3dB"))     
                    fig.add_trace(go.Scatter(x=[i/1e9 for i in vdf.FR_fHz[i]],y=vdf.FR_Response[i], mode='lines',name=name+"_Response"))  

    fig.update_layout(
        xaxis_title='f /GHz',
        yaxis_title='Frequency response /dB'
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8080)
    #http://127.0.0.1:8080/
    
'''    
    
    
