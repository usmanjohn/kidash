from flask import Blueprint

def register_blueprints(app):
    from .users.routes import users
    from .uploads.routes import uploads
    from .dashboard.routes import dash
    #from .others.routes import others

    app.register_blueprint(users, url_prefix='/users')
    app.register_blueprint(uploads, url_prefix='/')
    app.register_blueprint(dash, url_prefix='/dash')
    #app.register_blueprint(others, url_prefix='/others')

