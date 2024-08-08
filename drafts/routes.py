from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify
from forms import RegistrationForm, LoginForm
from werkzeug.utils import secure_filename
import boto3
from forms import UploadForm
from models import User, UploadSupport, UploadMain
from extensions import db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from application import create_app
from services.aws_client import upload_file_to_s3

    # Now you can safely use s3_client




web = Blueprint('web', __name__)  # Creating a blueprint named 'web'


#@web.context_processor
#def inject_upload_form():
#    return dict(form=UploadForm())

@web.route('/')
def home():
    form1 = UploadForm()
    form2 = UploadForm()
    return render_template('home.html', form1 = form1, form2 = form2)

@web.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('web.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Account created for {form.username.data}, You can login now!' , 'success')
        return redirect(url_for('web.login'))  # Ensure it refers to 'web.login'
    return render_template('register.html', title='Register', form=form)

@web.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('web.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('You are logged in!', 'success')
            return redirect(url_for('web.home'))
        else:
            flash('Login Unsuccessful, Please check email and password', 'danger')
            return redirect(url_for('web.login'))
        return redirect(url_for('web.home'))  # Ensure it refers to 'web.home'
    return render_template('login.html', title='Login', form=form)

@web.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('web.home'))


@web.route('/upload1', methods=['POST'])
@login_required
def upload_file_1():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            original_filename = secure_filename(file.filename)
            try:
                s3_key, new_filename = upload_file_to_s3(file, original_filename, folder = 'support_data')
                new_upload = UploadSupport(filename=new_filename, s3_key=s3_key, user_id=current_user.id)
                db.session.add(new_upload)
                db.session.commit()
                flash('File uploaded successfully.', 'success')
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'error')
    else:
        flash('Error in form submission.', 'error')
    
    return redirect(url_for('web.home'))

@web.route('/upload2', methods=['POST'])
@login_required
def upload_file_2():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            original_filename = secure_filename(file.filename)
            try:
                s3_key, new_filename = upload_file_to_s3(file, original_filename, folder='main_data')
                new_upload = UploadMain(filename=new_filename, s3_key=s3_key, user_id=current_user.id)
                db.session.add(new_upload)
                db.session.commit()
                print(f"New upload added to database: {new_upload}")  # Debug print
                flash(f'File uploaded successfully as {new_filename}.', 'success')
            except Exception as e:
                print(f"Error during upload: {str(e)}")  # Debug print
                db.session.rollback()  # Rollback the session in case of error
                flash(f'Error uploading file: {str(e)}', 'error')
    else:
        flash('Error in form submission.', 'error')
    
    return redirect(url_for('web.home'))

@web.route('/userdata')
def userdata():
    if current_user.is_authenticated:
        uploads = current_user.uploadsupport
        return render_template('userdata.html', uploads = uploads)
    else: return render_template('userdata.html')

@web.route('/check-uploads')
def check_uploads():
    try:
        uploads = UploadMain.query.all()
        print(f"Number of uploads fetched: {len(uploads)}")  # Debug print
        for upload in uploads:
            print(f"Upload: {upload}")  # Debug print
        return jsonify({'uploads': [{'id': u.id, 'filename': u.filename} for u in uploads]})
    except Exception as e:
        print(f"Error in check-uploads: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500
    
from services.aws_client import delete_file_from_s3

def delete_main_upload(upload_id):
    try:
        with db.session.begin_nested():  # Start a savepoint
            upload = UploadMain.query.get(upload_id)
            if not upload:
                return False, "Upload not found"

            # Delete from S3 first
            if not delete_file_from_s3(upload.s3_key):
                raise Exception("Failed to delete file from S3")

            # If S3 deletion was successful, delete from database
            db.session.delete(upload)
        
        # If we get here, both S3 and database deletions were successful
        db.session.commit()
        return True, "Upload deleted successfully"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting upload: {str(e)}")
        return False, str(e)
    
@web.route('/delete-main-upload/<int:upload_id>', methods=['POST', 'GET'])
@login_required
def delete_m_upload(upload_id):
    upload = UploadMain.query.get(upload_id)
    if not upload or upload.user_id != current_user.id:
        flash('Upload not found or you do not have permission to delete it.', 'error')
        return redirect(url_for('web.userdata'))

    success, message = delete_main_upload(upload_id)
    if success:
        flash('Upload deleted successfully.', 'success')
    else:
        flash(f'Error deleting upload: {message}', 'error')

    return redirect(url_for('web.userdata'))


def delete_support_upload(upload_id):
    try:
        with db.session.begin_nested():  # Start a savepoint
            upload = UploadSupport.query.get(upload_id)
            if not upload:
                return False, "Upload not found"

            # Delete from S3 first
            if not delete_file_from_s3(upload.s3_key):
                raise Exception("Failed to delete file from S3")

            # If S3 deletion was successful, delete from database
            db.session.delete(upload)
        
        # If we get here, both S3 and database deletions were successful
        db.session.commit()
        return True, "Upload deleted successfully"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting upload: {str(e)}")
        return False, str(e)
    
@web.route('/delete-support-upload/<int:upload_id>', methods=['POST', 'GET'])
@login_required
def delete_s_upload(upload_id):
    upload = UploadSupport.query.get(upload_id)
    if not upload or upload.user_id != current_user.id:
        flash('Upload not found or you do not have permission to delete it.', 'error')
        return redirect(url_for('web.userdata'))

    success, message = delete_support_upload(upload_id)
    if success:
        flash('Upload deleted successfully.', 'success')
    else:
        flash(f'Error deleting upload: {message}', 'error')

    return redirect(url_for('web.userdata'))