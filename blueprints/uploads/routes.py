from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from werkzeug.utils import secure_filename
from .forms import UploadForm
from models.models import UploadSupport, UploadMain, User
from extensions.extensions import db, cache
from sqlalchemy import desc
from flask_login import current_user, login_required
from services.aws_client import upload_file_to_s3, get_file_from_s3, get_static_data
from .functs import delete_upload
import pandas as pd
from io import BytesIO

from flask import current_app


uploads = Blueprint('uploads', __name__, template_folder='templates')

@uploads.context_processor
def inject_upload_form():
    return dict(form=UploadForm())


@cache.memoize(timeout=3600)
def get_cached_file_data(file_type, user_id, file_id=None):
    if file_type == 'main':
        if file_id:
            file = UploadMain.query.get(file_id)
        else:
            file = UploadMain.query.filter_by(user_id=user_id).order_by(desc(UploadMain.upload_date)).first()
    else:
        if file_id:
            file = UploadSupport.query.get(file_id)
        else:
            file = UploadSupport.query.filter_by(user_id=user_id).order_by(desc(UploadSupport.upload_date)).first()
    
    if file:
        return get_file_from_s3(file.s3_key), file.id
    return pd.DataFrame(), None


@uploads.route('/')
def home():
    support_html = ''
    main_html = ''
    if current_user.is_authenticated:
        support_files = UploadSupport.query.filter_by(user_id=current_user.id).order_by(desc(UploadSupport.upload_date)).all()
        main_files = UploadMain.query.filter_by(user_id=current_user.id).order_by(desc(UploadMain.upload_date)).all()
        
        try:
            main_data, selected_main_id = get_cached_file_data('main', current_user.id, session.get('selected_main_id'))
            support_data, selected_support_id = get_cached_file_data('support', current_user.id, session.get('selected_support_id'))
            
            # Update session with the latest file IDs if not already set
            if not session.get('selected_main_id') and main_files:
                session['selected_main_id'] = main_files[0].id
            if not session.get('selected_support_id') and support_files:
                session['selected_support_id'] = support_files[0].id
            
            support_html = support_data.head().to_html(classes='table table-striped', border=0) if not support_data.empty else ''
            main_html = main_data.head().to_html(classes='table table-striped', border=0) if not main_data.empty else ''
        except Exception as e:
            current_app.logger.error(f"Failed to process data: {str(e)}")
            support_html = ''
            main_html = ''
    else: 
        support_files = []
        main_files = []
        selected_main_id = None
        selected_support_id = None
        
    form1 = UploadForm()
    form2 = UploadForm()

    static_data = get_static_data()

    return render_template('home.html', form1=form1, form2=form2, support_files=support_files,
                           main_files=main_files, support_html=support_html, main_html=main_html,
                           static_data=static_data, selected_main_id=selected_main_id,
                           selected_support_id=selected_support_id)



@uploads.route('/select_file/<file_type>/<int:file_id>', methods=['GET'])
@login_required
def select_file(file_type, file_id):
    if file_type not in ['main', 'support']:
        flash('Invalid file type', 'error')
        return redirect(url_for('uploads.home'))

    # Clear the cache for the selected file type
    cache.delete_memoized(get_cached_file_data, file_type, current_user.id)

    # Update the session with the selected file ID
    session[f'selected_{file_type}_id'] = file_id

    # Update the cache with the new file data
    try:
        get_cached_file_data(file_type, current_user.id, file_id)
        flash(f'Successfully selected {file_type} file', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating cache: {str(e)}")
        flash('Error selecting file. Please try again.', 'error')

    return redirect(url_for('uploads.home'))


@uploads.route('/upload/<file_type>', methods=['POST'])
@login_required
def upload_file(file_type):
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            original_filename = secure_filename(file.filename)
            try:
                folder = 'support_data' if file_type == 'support' else 'main_data'
                s3_key, new_filename = upload_file_to_s3(file, original_filename, folder=folder)
                
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
                flash(f'Error uploading file: {str(e)}', 'error')
    else:
        flash('Error in form submission.', 'error')
    return redirect(url_for('uploads.home'))

@uploads.route('/delete-upload/<upload_type>/<int:upload_id>', methods=['POST'])
@login_required
def delete_upload_route(upload_type, upload_id):
    success, message = delete_upload(upload_id, upload_type)
    if success:
        flash('Upload deleted successfully.', 'success')
    else:
        flash(f'Error deleting upload: {message}', 'error')
    return redirect(url_for('uploads.home'))