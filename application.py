from flask import Flask
from extensions import login_manager, csrf, bcrypt, db
from dotenv import load_dotenv
from flask_migrate import Migrate

migrate = Migrate()

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from routes import web
    app.register_blueprint(web)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)