from models.models import User, UploadMain, UploadSupport
from flask import Blueprint, render_template
from flask_login import current_user
from services.aws_client import get_file_from_s3, get_static_data, get_cached_file_data
from functs.main_processor import DataProcessor
from functs.format_processor import format_processor
from functs.data_case_modify import data_case_fill
from dash import dash_table
from sqlalchemy import desc



dash = Blueprint('dash', __name__, template_folder='templates')
    

@dash.route('/dash')
def dashboard():
    main_html = ''
    if current_user.is_authenticated:
        try:
            main_data = get_cached_file_data('main', current_user.id)
            support_data = get_cached_file_data('support', current_user.id)
            static_data = get_static_data()
            sup_data = data_case_fill(support_data) 
            processor = DataProcessor(static_data)
            
            processor.load_data(main_data, sup_data)
            processor.process()
            print('Started main process')
            processed_df = processor.get_processed_data()
            processed_df = format_processor(processed_df)
            main_html = processed_df.to_html(classes='table table-striped', border=0) if not main_data.empty else ''
        except:
            'No data'
    return render_template('dashboard.html', main_html = main_html)