from io import BytesIO
import boto3
from flask import current_app
import datetime
import os
import io
import pandas as pd
from extensions.extensions import cache
from models.models import UploadMain, UploadSupport, ProcessedMain, ProcessedSupport
from sqlalchemy import desc


def upload_file_to_s3(file, filename, folder=''):
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
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
    

@cache.memoize(timeout=3600)
def get_cached_file_data(file_type, user_id):
    if file_type == 'main':    
        file = UploadMain.query.filter_by(user_id=user_id).order_by(desc(UploadMain.upload_date)).first()
    elif file_type == 'processed_main':    
        file = ProcessedMain.query.filter_by(user_id=user_id).order_by(desc(ProcessedMain.upload_date)).first()
    elif file_type == 'processed_support':    
        file = ProcessedSupport.query.filter_by(user_id=user_id).order_by(desc(ProcessedSupport.upload_date)).first()
    elif file_type == 'support':
        file = UploadSupport.query.filter_by(user_id=user_id).order_by(desc(UploadSupport.upload_date)).first()
    else:
        pass
    if file:
        return get_file_from_s3(file.s3_key)
    return pd.DataFrame()

file_paths = {
    'commission_rate': 'prep/commission_rate.xlsx',
    'retention_rate': 'prep/retention_rate.xlsx',
    'ins_retention_rate': 'prep/ins_retention_rate.xlsx',
    'working_data': 'prep/m5_working_data.xlsx',
    'data_case_sample': 'prep/sample_data_case.xlsx',
    'main_data_sample': 'prep/sample_main_data.xlsx',
    
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


def create_excel_file(df, filename):
    """Helper function to create an Excel file from a DataFrame"""
    from io import BytesIO
    import openpyxl

    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return output, filename