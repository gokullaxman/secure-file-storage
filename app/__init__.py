import os
from flask import Flask
from config import config
from .extensions import db, login_manager, bcrypt, csrf, limiter

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'error'
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
    # Register blueprints
    from .auth import auth_bp
    from .main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    # Ensure database is created
    with app.app_context():
        db.create_all()
        
    return app
