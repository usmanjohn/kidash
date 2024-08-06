import pandas as pd
pd.options.mode.chained_assignment = None


class DataProcessor:
    def __init__(self, static_data):
        self.process_data = None
        
        for key, value in static_data.items():
            setattr(self, key, value)

    def load_data(self,  main_data):
        
        self.process_data = main_data
        print("Loaded this month data")
    
    
    def preprocess_data(self):
        
        self.process_data.columns = self.process_data.columns.map(lambda x: f"{x[0]}_{x[1]}" if x[1] else f"{x[0]}")
        self.process_data.columns = ['Company_Month_Product_key', 'EndMonth', 'CompanyName']
        print("renamed columns")
        self.process_data['PerformanceMonth'] = self.process_data.apply(lambda x: x['Company_Month_Product_key'].split('/'), axis = 1).str[1]
        self.process_data['PerformanceMonth'] = pd.to_datetime(self.process_data['PerformanceMonth'], format = '%Y%m', errors = 'coerce')

        self.process_data['EndMonth'] = pd.to_datetime(self.process_data['EndMonth'], errors = 'coerce', format = '%Y%m')
        self.process_data['CurrentInstallment'] = self.process_data['EndMonth'].dt.to_period('M').astype(int)-self.process_data['PerformanceMonth'].dt.to_period('M').astype(int)+1
        print("modified date columns")

    def update_base_df(self, add_df, match_columns_base,match_columns_add, value_column, new_column_name):
        
        self.process_data['_temp_key'] = list(zip(*[self.process_data[col] for col in match_columns_base]))
        add_df['_temp_key'] = list(zip(*[add_df[col] for col in match_columns_add]))
        value_dict = add_df.groupby('_temp_key')[value_column].first().to_dict()
        self.process_data[new_column_name] = self.process_data['_temp_key'].map(value_dict)
        self.process_data.drop('_temp_key', axis=1, inplace=True)
        add_df.drop('_temp_key', axis=1, inplace=True)
        return self.process_data

    def lookup_value(self, lookup_df, base_company_col, look_company_col,  number_col, value_cols, add_str_to_col):
        def find_value(row):
            company = row[base_company_col]
            number = row[number_col]
            matches = lookup_df[lookup_df[look_company_col] == company]
            if not matches.empty:
                for col in value_cols:
                    if number <= col:
                        return matches[add_str_to_col+str(col)].iloc[0]
            
            return 0  
    
        return self.process_data.apply(find_value, axis=1)

    def sum_by_company_date(self, add_df, match_columns_base,match_columns_add, value_column, new_column_name):
        self.process_data['_temp_key'] = list(zip(*[self.process_data[col] for col in match_columns_base]))
        add_df['_temp_key'] = list(zip(*[add_df[col] for col in match_columns_add]))
        
        value_dict = add_df.groupby('_temp_key')[value_column].sum().to_dict()
        self.process_data[new_column_name] = self.process_data['_temp_key'].map(value_dict).fillna(0)
        
        self.process_data.drop('_temp_key', axis=1, inplace=True)
        add_df.drop('_temp_key', axis=1, inplace=True)
        
        return self.process_data

    def sum_col_company_date(self, add_df, match_columns_base,match_columns_add, value_column, new_column_name = 'alfa'):
        self.process_data['_temp_key'] = list(zip(*[self.process_data[col] for col in match_columns_base]))
        add_df['_temp_key'] = list(zip(*[add_df[col] for col in match_columns_add]))
        
        value_dict = add_df.groupby('_temp_key')[value_column].first().to_dict()
        
        self.process_data[new_column_name] = self.process_data['_temp_key'].map(value_dict).fillna(0)
        self.process_data.drop('_temp_key', axis = 1, inplace = True)
        
        return self.process_data[new_column_name]

    def process(self):
        print("Started calculations")
        self.preprocess_data()
        self.process_data = self.update_base_df(self.commission_rate, 
                                                ['CompanyName'], ['CompanyName'], 
                                                'Product Name Recognition Cycle', 
                                                'RevenueRecognitionInstallment')
        
        self.process_data = self.update_base_df(self.commission_rate,
                              ['CompanyName'],['CompanyName'], 
                              value_column = 'Performance Refund Rate', 
                              new_column_name = 'RefundRateAppliedInstallment')
        
        
        
        self.process_data['RefundRate'] = self.lookup_value(self.commission_rate, 'CompanyName', 'CompanyName', 
                                                            'CurrentInstallment', [i for i in range(25)], 
                                                            'Performance Commission ')/100
        self.process_data['RetentionRate'] = self.lookup_value(self.ins_retention_rate, 'CompanyName', 'InsuranceCompany', 
                                                            'CurrentInstallment', [i for i in range(25)], 
                                                            '')
        # Apply sum_by_company_date
        self.process_data = self.sum_by_company_date(self.data_case,
                                                     ['Company_Month_Product_key'], 
                                                     ['Insurance Company + Performance Month + Policy Installment Key'],
                                                     'Performance',
                                                     'Management_Performance(CurrentMonth)')
        
        self.process_data = self.sum_by_company_date(self.data_case,
                                   ['Company_Month_Product_key'], 
                                   ['Insurance Company + Performance Month + Policy Installment Key'],
                                   'Performance',
                                   'Management_Performance(CurrentMonth)')
        self.process_data = self.sum_by_company_date(self.data_case,
                                   ['Company_Month_Product_key'], 
                                   ['Insurance Company + Performance Month + Policy Installment Key'],
                                   'Contract Management',
                                   'Management_ContractManagement(CurrentMonth)')
        self.process_data = self.sum_by_company_date(self.data_case,
                                   ['Company_Month_Product_key'], 
                                   ['Insurance Company + Performance Month + Policy Installment Key'],
                                   'Collection',
                                   'Management_Collection(CurrentMonth)')
        self.process_data = self.sum_by_company_date(self.data_case,
                                   ['Company_Month_Product_key'], 
                                   ['Insurance Company + Performance Month + Policy Installment Key'],
                                   'Operations',
                                   'Management_Operation(CurrentMonth)')
        self.process_data = self.sum_by_company_date(self.data_case,
                                   ['Company_Month_Product_key'], 
                                   ['Insurance Company + Performance Month + Policy Installment Key'],
                                   'Others',
                                   'Management_Others(CurrentMonth)')
        
        cumulative_temp_data = self.sum_col_company_date(
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'CashCommissionManagement_Performance(Cumulative)')
                    
        self.process_data['Management_Performance(Cumulative)'] = self.process_data['Management_Performance(CurrentMonth)']+cumulative_temp_data
        cumulative_temp_data = self.sum_col_company_date( 
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'CashCommissionManagement_ContractManagement(Cumulative)')
                    
        self.process_data['ContractManagement(Cumulative)'] = self.process_data['Management_ContractManagement(CurrentMonth)']+cumulative_temp_data

        cumulative_temp_data = self.sum_col_company_date( 
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'CashCommissionManagement_Collection(Cumulative)') 
                    
        self.process_data['Management_Collection(Cumulative)'] = self.process_data['Management_Collection(CurrentMonth)']+cumulative_temp_data

        cumulative_temp_data = self.sum_col_company_date( 
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'CashCommissionManagement_Operation(Cumulative)') 
                  
        self.process_data['Management_Operation(Cumulative)'] = self.process_data['Management_Operation(CurrentMonth)']+cumulative_temp_data

        cumulative_temp_data = self.sum_col_company_date(
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'CashCommissionManagement_Others(Cumulative)') 
                    
        self.process_data['Management_Others(Cumulative)'] = self.process_data['Management_Others(CurrentMonth)']+cumulative_temp_data

        cumulative_temp_data = self.sum_col_company_date(
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'DeferredRevenue_EndingBalance') 
                    
        self.process_data['DeferredRevenue_BeginningBalance'] = cumulative_temp_data

        self.process_data['DeferredRevenue_CurrentMonthAmortization'] = self.process_data['Management_Performance(CurrentMonth)'] 
        self.process_data[self.process_data['Company_Month_Product_key']=='이관계약']['DeferredRevenue_CurrentMonthAmortization']=0

        self.process_data['DeferredRevenue_CumulativeRevenueRecognition(CurrentMonth)'] = self.process_data.apply(lambda x: 
                                                                                                x['CashCommissionManagement_Performance(Cumulative)'] 
                                                                                                if x['CurrentInstallment']>x['RevenueRecognitionInstallment'] 
                                                                                                else x['Management_Performance(Cumulative)']*
                                                                                                (x['CurrentInstallment']/x['RevenueRecognitionInstallment']), 
                                                                                               axis = 1)
        cumulative_temp_data = self.sum_col_company_date( 
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'DeferredRevenue_CumulativeRevenueRecognition(CurrentMonth)') 
                    
        self.process_data['DeferredRevenue_CumulativeRevenueRecognition(PreviousMonth)'] = cumulative_temp_data


        
        self.process_data['DeferredRevenue_RevenueRecognition(CurrentMonth)']=self.process_data['DeferredRevenue_CumulativeRevenueRecognition(CurrentMonth)'] - self.process_data['DeferredRevenue_CumulativeRevenueRecognition(PreviousMonth)']

        self.process_data['DeferredRevenue_OtherAdjustments'] = 0
        self.process_data['DeferredRevenue_EndingBalance'] = self.process_data.apply(lambda x: 
                                                                        0 if x['CurrentInstallment']>x['RevenueRecognitionInstallment'] 
                                                                        else x['Management_Performance(Cumulative)']-x['DeferredRevenue_CumulativeRevenueRecognition(CurrentMonth)'], 
                                                                       axis = 1)

        
        self.process_data['DeferredRevenue_OtherAdjustments'] = self.process_data['DeferredRevenue_EndingBalance']+self.process_data['DeferredRevenue_RevenueRecognition(CurrentMonth)']-self.process_data['DeferredRevenue_BeginningBalance']-self.process_data['DeferredRevenue_CurrentMonthAmortization']

        cumulative_temp_data = self.sum_col_company_date( 
                     add_df = self.working_data,
                    match_columns_base = ['Company_Month_Product_key'],
                    match_columns_add = ['InsuranceCompany_PerformanceMonth_ProductGroup_Key'],
                    value_column = 'RefundLiability_EndingBalance') 
                    
        self.process_data['RefundLiability_BeginningBalance'] = cumulative_temp_data

        self.process_data['RefundLiability_CurrentRevenueAdjustment'] = 0

        self.process_data['RefundLiability_EndingBalance'] = self.process_data.apply(lambda x: 
                0 if x['DeferredRevenue_EndingBalance'] == 0 else (
                    0 if x['CurrentInstallment'] > x['RevenueRecognitionInstallment'] else (
                        x['Management_Performance(Cumulative)'] * x['RefundRate'] * (1 - x['RetentionRate'])
                        if x['Management_Performance(Cumulative)'] * x['RefundRate'] * (1 - x['RetentionRate']) > 0
                        else 0
                    )
                ),
                axis=1
            ).round(1)

        self.process_data['RefundLiability_CurrentRevenueAdjustment'] = self.process_data['RefundLiability_EndingBalance']-self.process_data['RefundLiability_BeginningBalance']
        self.process_data.drop('alfa', axis=1, inplace = True)
        print("done")  
    
    def get_processed_data(self):
        return self.process_data
