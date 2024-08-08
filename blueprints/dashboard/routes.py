from models.models import User, UploadMain, UploadSupport
from flask import Blueprint, render_template
from flask_login import current_user
from services.aws_client import get_file_from_s3, get_static_data
from functs.main_processor import DataProcessor
from functs.format_processor import format_processor
from functs.data_case_modify import data_case_fill
from dash import dash_table
from sqlalchemy import desc



dash = Blueprint('dash', __name__, template_folder='templates')
    

@dash.route('/dash')
def dashboard():
    if current_user.is_authenticated:
        support_file = UploadSupport.query.filter_by(user_id=current_user.id).order_by(desc(UploadSupport.upload_date)).first()
        main_file = UploadMain.query.filter_by(user_id=current_user.id).order_by(desc(UploadMain.upload_date)).first()
        
        try:
            main_data = get_file_from_s3(main_file.s3_key)
            support_data = get_file_from_s3(support_file.s3_key)
            print('getting uploaded datas')
            print(main_file.s3_key)
            print('Support File:', support_file.s3_key)
            print(len(support_data.columns))
            support_data = data_case_fill(support_data)
            print('formatting sup data')
            
            static_data = get_static_data()
            print('got static data')
            processor = DataProcessor(static_data)
            
            processor.load_data(main_data, support_data)
            processor.process()
            print('Started main process')
            processed_df = processor.get_processed_data()
            processed_df = format_processor(processed_df)
            print(processed_df.head())
            
            #table = dash_table.DataTable(processed_df.to_dict('records'), [{"name": i, "id": i} for i in processed_df.columns])
        except:
            'No data'
        return render_template('dashboard.html')