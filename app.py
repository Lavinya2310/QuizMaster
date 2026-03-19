from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from datetime import datetime, date

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.user import user_bp
from routes.main import main_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(main_bp)

@app.context_processor
def utility_processor():
    def current_time():
        return datetime.now().date()  # or datetime.now() if you want time too
    return dict(current_time=current_time)

# Create database & default admin
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@gmail.com',
            role='admin',
            full_name='Administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)