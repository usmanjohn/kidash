import boto3
from flask import current_app
from datetime import datetime
import os

def upload_file_to_s3(file, filename, folder=''):
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # Split filename and extension
    name, ext = os.path.splitext(filename)
    
    # Create new filename with unique identifier and timestamp
    new_filename = f"{name}_{timestamp}{ext}"
    
    # Create the S3 key with the folder
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