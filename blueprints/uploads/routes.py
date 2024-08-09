from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session,make_response, send_file
from werkzeug.utils import secure_filename
from .forms import UploadForm
from models.models import UploadSupport, UploadMain, ProcessedMain, ProcessedSupport
from extensions.extensions import db, cache
from sqlalchemy import desc
from flask_login import current_user, login_required
from services.aws_client import upload_file_to_s3, get_file_from_s3, get_static_data, get_cached_file_data
from .functs import delete_upload
import pandas as pd
import boto3
import datetime
from functs.data_case_modify import data_case_fill
from functs.main_processor import DataProcessor
from functs.format_processor import format_processor
from functs.sample_datas import sample_data

from io import BytesIO

from flask import current_app


uploads = Blueprint('uploads', __name__, template_folder='templates')

@uploads.context_processor
def inject_upload_form():
    return dict(form=UploadForm())




@uploads.route('/')
def home():
    support_html = ''
    main_html = ''
    if current_user.is_authenticated:
        try:
            main_data = get_cached_file_data('main', current_user.id)
            support_data = get_cached_file_data('support', current_user.id)
            

            support_html = support_data.head().to_html(classes='table table-striped', border=0) if not support_data.empty else ''
            main_html = main_data.head().to_html(classes='table table-striped', border=0) if not main_data.empty else ''
        except Exception as e:
            current_app.logger.error(f"Failed to process data: {str(e)}")
            support_html = ''
            main_html = ''
        
    form1 = UploadForm()
    form2 = UploadForm()
    return render_template('home.html', form1=form1, form2=form2, support_html=support_html, main_html=main_html)

def process_support_data():
    support_data = get_cached_file_data('support', current_user.id)
    return data_case_fill(support_data)

def process_main_data():
    main_data = get_cached_file_data('main', current_user.id)
    processed_support = get_cached_file_data('processed_support', current_user.id)
    static_data = get_static_data()
    processor = DataProcessor(static_data)
    processor.load_data(main_data, processed_support)
    processor.process()
    
    processed_main = processor.get_processed_data()
    return format_processor(processed_main)

@uploads.route('/process/<file_type>', methods=['POST', "GET"])
def process_data(file_type):
    try:
        if file_type == 'support':
            processed_data = process_support_data()
            upload_file_type = 'processed_support'
        elif file_type == 'main':
            processed_data = process_main_data()
            upload_file_type = 'processed_main'
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        upload_processed_data(processed_data, upload_file_type)
        
        # Clear the cache for the processed file type
        cache.delete_memoized(get_cached_file_data, upload_file_type, current_user.id)
        
        
        return jsonify({'success': True, 'message': f'{file_type.capitalize()} data processed successfully'})
    except Exception as e:
        current_app.logger.error(f"Error processing {file_type} data: {str(e)}")
        return jsonify({'error': str(e)}), 500

def upload_processed_data(data, file_type):
    filename = f'{"건별" if file_type == "processed_support" else "당월"}데이터.xlsx'
    folder = file_type
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False)
    output.seek(0)
    
    s3_key, new_filename = upload_file_to_s3(output, filename, folder=folder)
    
    if file_type == 'processed_support':
        new_upload = ProcessedSupport(filename=new_filename, s3_key=s3_key, user_id=current_user.id)
    elif file_type == 'processed_main':
        new_upload = ProcessedMain(filename=new_filename, s3_key=s3_key, user_id=current_user.id)
    else:
        raise ValueError(f"Invalid file type: {file_type}")
    
    db.session.add(new_upload)
    db.session.commit()

@uploads.route('/download/<file_type>',methods=['POST', "GET"])
def download_processed(file_type):
    if file_type not in ['processed_support', 'processed_main']:
        return jsonify({'error': 'Invalid file type'}), 400
    
    latest_processed = get_cached_file_data(file_type, current_user.id)
    if latest_processed is None or latest_processed.empty:
        return jsonify({'error': f'No processed {file_type} data available'}), 404
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        latest_processed.to_excel(writer, index=False)
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"{file_type.replace('processed_', '')}_data.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@uploads.route('/upload/<file_type>', methods=['POST'])
@login_required
def upload_file(file_type):
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            try:
                # Read the file into a pandas DataFrame
                df = pd.read_excel(file)
                if file_type == 'support' and len(df.columns) != 33:
                    flash(f'건별데이터 파일에는 정확히 33개의 열이 있어야 합니다. 이 파일에는 {len(df.columns)} 개의 열이 있습니다.', 'danger')
                    return redirect(url_for('uploads.home'))
                elif file_type == 'main' and len(df.columns) != 3:
                    flash(f'당월데이터 파일에는 정확히 3개의 열이 있어야 합니다. 이 파일에는 {len(df.columns)} 개의 열이 있습니다.', 'danger')
                    return redirect(url_for('uploads.home'))
                
                # If we've passed the column check, proceed with upload
                original_filename = secure_filename(file.filename)
                folder = 'support_data' if file_type == 'support' else 'main_data'
                
                # Convert DataFrame back to Excel file
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)
                
                s3_key, new_filename = upload_file_to_s3(output, original_filename, folder=folder)
                
                if file_type == 'support':
                    new_upload = UploadSupport(filename=new_filename, s3_key=s3_key, user_id=current_user.id)
                else:
                    new_upload = UploadMain(filename=new_filename, s3_key=s3_key, user_id=current_user.id)
                
                db.session.add(new_upload)
                db.session.commit()
                
                # Update the session with the new file ID
                session[f'selected_{file_type}_id'] = new_upload.id
                
                # Clear the cache for this file type
                cache.delete_memoized(get_cached_file_data, file_type, current_user.id)
                
                flash(f'File uploaded successfully as {new_filename}.', 'success')
            except Exception as e:
                flash(f'Error processing or uploading file: {str(e)}', 'danger')
    else:
        flash('Error in form submission.', 'danger')
    return redirect(url_for('uploads.home'))

@uploads.route('/delete-upload/<upload_type>/<int:upload_id>', methods=['POST'])
@login_required
def delete_upload_route(upload_type, upload_id):
    success, message = delete_upload(upload_id, upload_type)
    if success:
        flash('Upload deleted successfully.', 'success')
    else:
        flash(f'Error deleting upload: {message}', 'danger')
    return redirect(url_for('uploads.home'))

@uploads.route('/download-sample/<sample_name>')
def download_sample(sample_name):
    df = sample_data(sample_name)
    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_file.seek(0)
    response = make_response(excel_file.read())
    response.headers.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response.headers.set('Content-Disposition', 'attachment', filename=f"{sample_name}.xlsx")
    return response
