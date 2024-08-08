from models.models import UploadMain, UploadSupport
from services.aws_client import delete_file_from_s3
from flask_login import current_user
from extensions.extensions import db
from flask import current_app

def delete_upload(upload_id, upload_type):
    if upload_type == 'main':
        upload_class = UploadMain
    elif upload_type == 'support':
        upload_class = UploadSupport
    else:
        return False, "Invalid upload type specified"

    upload = upload_class.query.get(upload_id)
    if not upload:
        return False, "Upload not found"

    if upload.user_id != current_user.id:
        return False, "Not authorized to delete this upload"

    try:
        with db.session.begin_nested():
            if delete_file_from_s3(upload.s3_key):
                db.session.delete(upload)
                db.session.commit()
                return True, "Upload deleted successfully"
            else:
                raise Exception("Failed to delete file from S3")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting upload: {str(e)}")
        return False, str(e)