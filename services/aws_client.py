from io import BytesIO
import boto3
from flask import current_app
from datetime import datetime
import os
import io
import pandas as pd
from extensions.extensions import cache


def upload_file_to_s3(file, filename, folder=''):
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_{timestamp}{ext}"
    if folder:
        s3_key = f"{folder}/{new_filename}"
    else:
        s3_key = new_filename
    s3.upload_fileobj(
        file,
        current_app.config['S3_BUCKET'],
        s3_key,
        ExtraArgs={'ACL': 'private'}
    )
    return s3_key, new_filename

def delete_file_from_s3(s3_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    
    try:
        s3.delete_object(Bucket=current_app.config['S3_BUCKET'], Key=s3_key)
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting file from S3: {str(e)}")
        return False

@cache.memoize(timeout=3600)    
def get_file_from_s3(s3_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )

    try:
        # Get the object from S3
        response = s3.get_object(Bucket=current_app.config['S3_BUCKET'], Key=s3_key)
        # Read the object's content into Pandas DataFrame
        data = response['Body'].read()
        df = pd.read_excel(BytesIO(data))
        return df
    except Exception as e:
        current_app.logger.error(f"Failed to read from S3: {str(e)}")
        return None 
    

file_paths = {
    'commission_rate': 'prep/commission_rate.xlsx',
    'retention_rate': 'prep/retention_rate.xlsx',
    'ins_retention_rate': 'prep/ins_retention_rate.xlsx',
    'working_data': 'prep/m5_working_data.xlsx'
}
@cache.cached(timeout=3600, key_prefix='static_data')
def load_static_data():
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    print("Loading static data...")
    static_data = {}
    for key, path in file_paths.items():
        obj = s3.get_object(Bucket=current_app.config['S3_BUCKET'], Key=path)
        static_data[key] = pd.read_excel(io.BytesIO(obj['Body'].read()))
    print("Static data loaded successfully")
    return static_data

def get_static_data():
    return load_static_data()




from flask import session
from models.models import User
from extensions.extensions import db

def update_user_file_selection(user_id, file_s3_key, file_type):
    user = User.query.get(user_id)
    if user:
        if file_type == 'main':
            user.current_main_file_s3_key = file_s3_key
        elif file_type == 'support':
            user.current_support_file_s3_key = file_s3_key
        db.session.commit()