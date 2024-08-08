import datetime
import pandas as pd
import numpy as np
def data_case_fill(data_case):
    translated_columns = [
        'Closing Month', 'Insurance Company', 'Recruiter Code', 'Policy Number', 'Contract Date', 
        'Payment Method', 'Contract Status', 'Payment Installment',
        'Calculation Method', 'Premium', 'Monthly Premium', 'Settlement Performance',
        'Conversion Performance 1', 'Conversion Performance 2', 'Conversion Performance 3', 'Performance',
        'Contract Management', 'Collection', 'Operations', 'Others', 'Total', 'Payment Period',
        'Product Group', 'Product Code', 'Product Name', 'Policyholder',
        'Insured Person', 'Fetus Installment', 'Fetus Status', 'ERP Employee Number',
        'Employee Name', 'Recruiter Affiliation Path Business Unit', 'Recruiter Affiliation Path Branch/Team',
    ]
    try:
        data_case.columns = translated_columns
        print('changed columns')
        data_case = data_case.iloc[:80438]
        print('Sliced')
        data_case['Contract Date']=pd.to_datetime(data_case['Contract Date'], errors = 'coerce').dt.date
        print('1')
        data_case['Contract Date'] = data_case['Contract Date'].fillna(datetime.date(2000, 1, 1))
        print('2')
        data_case['Transfer Contract Status'] = data_case['Contract Date'].apply(lambda x: "이관계약" if x  < datetime.date(2023, 7, 1) else "회사보유계약")
        print('3')
        data_case['Insurance Company 1'] = data_case['Insurance Company']
        data_case['Performance Month']=data_case['Contract Date'].astype(str).str.replace('-', '').str[:6]
        data_case['Product Group Classification'] = 'Not given'


        data_case['Insurance Company + Performance Month + Policy Installment Key']=data_case.apply(lambda x: x['Insurance Company 1']+'/'+ x['Performance Month'] 
                                                                                                    if x['Transfer Contract Status']=='회사보유계약' 
                                                                                                    else x['Transfer Contract Status'], axis = 1)
        return data_case

    except:
        print('Data did not meet format reuirements ')