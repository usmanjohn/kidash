from dash import Dash, dcc, html, dash_table, Input, Output, callback, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from style import data_table_styles

import math
import plotly.express as px

def format_processor(df):
    cols_korean = ['보험사+업적월+상품군 key','마감월', '보험사', '업적월', '당기해당회차', '수익비용인식회차','환수율적용회차','환수율', '유지율', '성과(당월)', '계약관리(당월)', '수금(당월)', '운영(당월)', 
               '기타(당월)', '성과(누적)', '계약관리(누적)', '수금(누적)', '운영(누적)', '기타(누적)', '기초선수수익', '당월정액상각대상수령액', '당월누적수익인식액', '전월누적수익인식액',
               '당월수익인식액', '기타조정액', '기말선수수익', '기초환수부채', '당기환수수익조정', '기말환수부채']
    
    if len(df.columns)==29:
        df.columns = cols_korean
        df['마감월'] = df['마감월'].dt.date        
        df['업적월'] = df['업적월'].dt.date
        df['환수율'] = df['환수율'].round(2) 
        df['유지율'] = df['유지율'].round(2)  
    return df

    #df.to_excel('result/m_6_working_data.xlsx', index = False)


#data_df = pd.read_excel('result/m_6_working_data.xlsx')
#ready_df_download = format_modify(data_df)
#df = ready_df_download.copy()
#df[['환수율','유지율']] = np.round(df[['환수율','유지율']]*100)
#df = df.round(0) 
#df[['환수율','유지율']] = df[['환수율','유지율']].astype(str)+ ' %' 
PAGE_SIZE = 10
#df_a = df.fillna(0)
#print(df.isna().sum())

def create_data_table(data):
    return dash_table.DataTable(
        
        data=data.to_dict('records'),
        columns=[{"name": i, "id": i} for i in data.columns],
        
        **data_table_styles,
        
    )