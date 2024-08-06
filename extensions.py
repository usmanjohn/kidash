from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

bcrypt = Bcrypt()
db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()