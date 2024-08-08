
from extensions.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    current_support_file_s3_key = db.Column(db.String(256), nullable=True)
    current_main_file_s3_key = db.Column(db.String(256), nullable=True)

    uploadsupport = db.relationship('UploadSupport', backref='user', lazy=True)
    uploadmain = db.relationship('UploadMain', backref='user', lazy=True)

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    
class UploadSupport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    s3_key = db.Column(db.String(256), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Assuming you have a User model

    def __repr__(self):
        return f'<Upload {self.filename}>'

class UploadMain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    s3_key = db.Column(db.String(256), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Assuming you have a User model

    def __repr__(self):
        return f'<Upload {self.filename}>'
