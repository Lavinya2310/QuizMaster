from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Subject, Chapter, Quiz, Question, Score, User
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    def wrap(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    subjects = Subject.query.all()
    total_users = User.query.filter_by(role='user').count()
    total_quizzes = Quiz.query.count()
    total_attempts = Score.query.count()

    # Prepare chart data
    subject_labels = []
    quiz_counts = []
    avg_scores = []
    attempt_counts = []

    for subj in subjects:
        subject_labels.append(subj.name)
        
        subj_quizzes = Quiz.query.join(Chapter).filter(Chapter.subject_id == subj.id).count()
        quiz_counts.append(subj_quizzes)
        
        subj_scores = db.session.query(db.func.avg(Score.score * 100.0 / Score.total))\
            .join(Quiz).join(Chapter)\
            .filter(Chapter.subject_id == subj.id)\
            .scalar() or 0
        avg_scores.append(round(subj_scores, 1))
        
        subj_attempts = Score.query.join(Quiz).join(Chapter)\
            .filter(Chapter.subject_id == subj.id).count()
        attempt_counts.append(subj_attempts)

    return render_template(
        'admin/dashboard.html',
        subjects=subjects,
        total_users=total_users,
        total_quizzes=total_quizzes,
        total_attempts=total_attempts,
        subject_labels=subject_labels,
        quiz_counts=quiz_counts,
        avg_scores=avg_scores,
        attempt_counts=attempt_counts
    )

# Subjects CRUD
@admin_bp.route('/subjects')
@login_required
@admin_required
def subjects():
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@admin_bp.route('/subject/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_subject():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Subject name is required', 'danger')
            return render_template('admin/subject_form.html')
        
        if Subject.query.filter_by(name=name).first():
            flash('Subject name already exists', 'danger')
            return render_template('admin/subject_form.html')
        
        subject = Subject(name=name, description=description)
        db.session.add(subject)
        db.session.commit()
        flash('Subject created successfully!', 'success')
        return redirect(url_for('admin.subjects'))
    
    return render_template('admin/subject_form.html')

@admin_bp.route('/subject/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Subject name is required', 'danger')
            return render_template('admin/subject_form.html', subject=subject)
        
        if name != subject.name and Subject.query.filter_by(name=name).first():
            flash('Subject name already exists', 'danger')
            return render_template('admin/subject_form.html', subject=subject)
        
        subject.name = name
        subject.description = description
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin.subjects'))
    
    return render_template('admin/subject_form.html', subject=subject)

@admin_bp.route('/subject/delete/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    name = subject.name  # for flash message
    
    db.session.delete(subject)
    db.session.commit()
    flash(f'Subject "{name}" deleted successfully!', 'info')
    return redirect(url_for('admin.subjects'))

# Chapters CRUD
@admin_bp.route('/chapters/<int:subject_id>')
@login_required
@admin_required
def chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('admin/chapters.html', subject=subject, chapters=chapters)

@admin_bp.route('/chapter/new/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def new_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if name:
            chapter = Chapter(name=name, description=description, subject_id=subject.id)
            db.session.add(chapter)
            db.session.commit()
            flash('Chapter created successfully', 'success')
            return redirect(url_for('admin.chapters', subject_id=subject.id))
        flash('Chapter name is required', 'danger')
    return render_template('admin/chapter_form.html', subject=subject)

@admin_bp.route('/chapter/edit/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    subject = chapter.subject
    if request.method == 'POST':
        chapter.name = request.form.get('name')
        chapter.description = request.form.get('description')
        db.session.commit()
        flash('Chapter updated', 'success')
        return redirect(url_for('admin.chapters', subject_id=subject.id))
    return render_template('admin/chapter_form.html', chapter=chapter, subject=subject)

@admin_bp.route('/chapter/delete/<int:chapter_id>', methods=['POST'])
@login_required
@admin_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Check if any quiz in this chapter has scores
    has_scores = db.session.query(Score.id).join(Quiz).filter(Quiz.chapter_id == chapter_id).first()
    
    if has_scores:
        flash("Cannot delete this chapter — some quizzes have user scores. Delete scores or quizzes first.", "danger")
        return redirect(url_for('admin.chapters', subject_id=chapter.subject_id))
    
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted', "success")
    return redirect(url_for('admin.chapters', subject_id=chapter.subject_id))

# Quizzes CRUD
@admin_bp.route('/quizzes/<int:chapter_id>')
@login_required
@admin_required
def quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes_list = Quiz.query.filter_by(chapter_id=chapter_id).order_by(Quiz.id.desc()).all()
    return render_template('admin/quizzes.html', chapter=chapter, quizzes=quizzes_list)

@admin_bp.route('/quiz/new/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def new_quiz(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        duration = request.form.get('duration_minutes', type=int)
        date_str = request.form.get('scheduled_date')

        if not title or not duration or duration < 5:
            flash('Title and valid duration (≥5 min) are required', 'danger')
            return redirect(request.url)

        scheduled_date = None
        if date_str:
            try:
                scheduled_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format', 'danger')
                return redirect(request.url)

        quiz = Quiz(
            title=title,
            chapter_id=chapter.id,
            duration_minutes=duration,
            scheduled_date=scheduled_date
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz created successfully', 'success')
        return redirect(url_for('admin.quizzes', chapter_id=chapter.id))

    return render_template('admin/quiz_form.html', chapter=chapter)

@admin_bp.route('/quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter = quiz.chapter

    if request.method == 'POST':
        quiz.title = request.form.get('title', '').strip()
        quiz.duration_minutes = request.form.get('duration_minutes', type=int)
        date_str = request.form.get('scheduled_date')

        scheduled_date = None
        if date_str:
            try:
                scheduled_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format', 'danger')
                return redirect(request.url)

        quiz.scheduled_date = scheduled_date

        db.session.commit()
        flash('Quiz updated', 'success')
        return redirect(url_for('admin.quizzes', chapter_id=chapter.id))

    return render_template('admin/quiz_form.html', quiz=quiz, chapter=chapter)

@admin_bp.route('/quiz/delete/<int:quiz_id>', methods=['POST'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter_id
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted', 'info')
    return redirect(url_for('admin.quizzes', chapter_id=chapter_id))

# Questions CRUD
@admin_bp.route('/questions/<int:quiz_id>')
@login_required
@admin_required
def questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('admin/questions.html', quiz=quiz)

@admin_bp.route('/question/new/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def new_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        opt1 = request.form.get('option1', '').strip()
        opt2 = request.form.get('option2', '').strip()
        opt3 = request.form.get('option3', '').strip()
        opt4 = request.form.get('option4', '').strip()
        correct = request.form.get('correct_option', type=int)

        if not text or not opt1 or not opt2 or correct is None:
            flash('Question text, at least two options, and correct answer are required', 'danger')
            return redirect(request.url)

        question = Question(
            quiz_id=quiz.id,
            text=text,
            option1=opt1,
            option2=opt2,
            option3=opt3 or None,
            option4=opt4 or None,
            correct_option=correct
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully', 'success')
        return redirect(url_for('admin.questions', quiz_id=quiz.id))

    return render_template('admin/question_form.html', quiz=quiz)

@admin_bp.route('/question/edit/<int:question_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz = question.quiz

    if request.method == 'POST':
        question.text = request.form.get('text', '').strip()
        question.option1 = request.form.get('option1', '').strip()
        question.option2 = request.form.get('option2', '').strip()
        question.option3 = request.form.get('option3', '').strip() or None
        question.option4 = request.form.get('option4', '').strip() or None
        question.correct_option = request.form.get('correct_option', type=int)

        db.session.commit()
        flash('Question updated', 'success')
        return redirect(url_for('admin.questions', quiz_id=quiz.id))

    return render_template('admin/question_form.html', question=question, quiz=quiz)

@admin_bp.route('/question/delete/<int:question_id>', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted', 'info')
    return redirect(url_for('admin.questions', quiz_id=quiz_id))