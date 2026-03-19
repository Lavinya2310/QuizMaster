import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-change-me-2026'
    
    # ────────────────────────────────────────────────
    # Use this version (absolute + ensures folder exists)
    # ────────────────────────────────────────────────
    INSTANCE_DIR = os.path.join(basedir, 'instance')
    os.makedirs(INSTANCE_DIR, exist_ok=True)           # Create folder if missing
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'quiz.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False