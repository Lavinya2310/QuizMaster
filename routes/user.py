from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Quiz, Question, Score, Chapter, Subject
from datetime import datetime
from datetime import date
from sqlalchemy import func

user_bp = Blueprint('user', __name__)

def user_required(f):
    """Decorator: only allow regular users (not admin)"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'user':
            flash("This area is for registered users only.", "warning")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    # Last 5 attempts, newest first
    recent_scores = Score.query.filter_by(user_id=current_user.id)\
                               .join(Quiz)\
                               .order_by(Score.attempted_at.desc())\
                               .limit(5).all()

    return render_template(
        'user/dashboard.html',
        recent_scores=recent_scores
    )


@user_bp.route('/upcoming')
@login_required
@user_required
def upcoming():
    # List all available quizzes
    quizzes = Quiz.query.join(Chapter).join(Subject)\
                  .order_by(Quiz.scheduled_date.desc(), Quiz.title).all()
    
    return render_template('user/upcoming_quizzes.html', quizzes=quizzes)


@user_bp.route('/take_quiz/<int:quiz_id>')
@login_required
@user_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check scheduled date
    today = date.today()
    if quiz.scheduled_date and quiz.scheduled_date > today:
        flash(f"This quiz is scheduled for {quiz.scheduled_date.strftime('%d/%m/%Y')}. You cannot attempt it yet.", "warning")
        return redirect(url_for('user.upcoming'))
    
    # Optional: also check if already attempted
    if Score.query.filter_by(user_id=current_user.id, quiz_id=quiz.id).first():
        flash("You have already attempted this quiz.", "info")
        return redirect(url_for('user.scores'))
    
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    if not questions:
        flash("This quiz has no questions yet.", "warning")
        return redirect(url_for('user.upcoming'))
    
    return render_template('user/take_quiz.html', quiz=quiz, questions=questions)


@user_bp.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
@user_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    
    if not questions:
        flash("Cannot submit an empty quiz.", "danger")
        return redirect(url_for('user.take_quiz', quiz_id=quiz_id))
    
    total = len(questions)
    correct = 0
    
    for q in questions:
        answer_key = f"answer_{q.id}"
        selected = request.form.get(answer_key)
        if selected and int(selected) == q.correct_option:
            correct += 1
    
    score = Score(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=correct,
        total=total,
        attempted_at=datetime.utcnow()
    )
    
    db.session.add(score)
    db.session.commit()
    
    percentage = (correct / total * 100) if total > 0 else 0
    flash(f"Quiz submitted! You scored {correct}/{total} ({percentage:.1f}%)", "success")
    
    return redirect(url_for('user.scores'))


@user_bp.route('/scores')
@login_required
@user_required
def scores():
    user_scores = Score.query.filter_by(user_id=current_user.id)\
                             .join(Quiz)\
                             .order_by(Score.attempted_at.desc())\
                             .all()
    
    return render_template('user/scores.html', scores=user_scores)


@user_bp.route('/summary')
@login_required
@user_required
def summary():
    scores = Score.query.filter_by(user_id=current_user.id).all()

    has_data = bool(scores)

    if not has_data:
        return render_template(
            'user/summary.html',
            has_data=False,
            total_correct=0,
            total_questions=0,
            user_subject_labels=[],
            user_subject_averages=[],
            attempt_dates=[],
            attempt_percents=[]
        )

    # ── real calculations when there is data ──
    total_correct = sum(s.score for s in scores)
    total_questions = sum(s.total for s in scores)

    # Subject stats
    from sqlalchemy import func
    subject_stats = db.session.query(
        Subject.name,
        func.avg(Score.score * 100.0 / Score.total).label('avg'),
        func.count(Score.id).label('count')
    ).join(Quiz, Score.quiz_id == Quiz.id)\
     .join(Chapter, Quiz.chapter_id == Chapter.id)\
     .join(Subject, Chapter.subject_id == Subject.id)\
     .filter(Score.user_id == current_user.id)\
     .group_by(Subject.name).all()

    user_subject_labels = [row.name for row in subject_stats]
    user_subject_averages = [round(row.avg or 0, 1) for row in subject_stats]

    # Recent attempts
    recent = sorted(scores, key=lambda s: s.attempted_at, reverse=True)[:10]
    attempt_dates = [s.attempted_at.strftime('%b %d') for s in recent]
    attempt_percents = [round(s.score / s.total * 100, 1) if s.total > 0 else 0 for s in recent]

    return render_template(
    'user/summary.html',
    has_data=has_data,
    scores=scores,                 
    total_correct=total_correct,
    total_questions=total_questions,
    user_subject_labels=user_subject_labels,
    user_subject_averages=user_subject_averages,
    attempt_dates=attempt_dates,
    attempt_percents=attempt_percents
)