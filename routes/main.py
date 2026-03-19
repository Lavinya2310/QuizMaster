from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
@main_bp.route('/home')
def index():
    """
    Landing / home page — redirects based on authentication & role.
    This is the root route most users will hit first.
    """
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    
    # Not logged in → show welcome / landing page
    return render_template('main/index.html')


@main_bp.route('/about')
def about():
    """Optional simple about page"""
    return render_template('main/about.html')


# You can add more public routes here if needed, e.g.
# @main_bp.route('/contact')
# def contact():
#     return render_template('main/contact.html')