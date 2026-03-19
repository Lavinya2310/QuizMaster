from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        login_input = request.form.get('username')      # from the form
        password = request.form.get('password')

        if not login_input or not password:
            flash('Please enter username/email and password', 'danger')
            return render_template('auth/login.html')

        # Try to find user by username OR by email
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username/email or password', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('username', '').strip()     # using same field for simplicity
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        qualification = request.form.get('qualification', '').strip()
        dob_str = request.form.get('dob', '').strip()

        # Basic validation
        errors = []
        if not username or '@' not in username:
            errors.append("Please enter a valid email as username")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters")
        
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register.html')

        # Convert DOB string → date object
        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid date format for DOB (use YYYY-MM-DD)", 'danger')
                return render_template('auth/register.html')

        # Check duplicates
        if User.query.filter_by(username=username).first():
            flash('This email is already registered', 'danger')
            return render_template('auth/register.html')

        # Create user
        user = User(
            username=username,
            email=email,                     # same as username in this setup
            full_name=full_name or None,
            qualification=qualification or None,
            dob=dob,
            role='user'
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))