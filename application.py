from flask import Flask
from extensions.extensions import login_manager, csrf, bcrypt, db, cache
from dotenv import load_dotenv
from flask_migrate import Migrate

migrate = Migrate()

load_dotenv()
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Configure cache with the app instance
    cache.init_app(app, config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 3600
    })

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from blueprints import register_blueprints
    register_blueprints(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)