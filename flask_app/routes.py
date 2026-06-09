from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_app import app, db, bcrypt
from flask_app.forms import RegistrationForm, LoginForm
from flask_app.models import User, Progress, Sentence
from flask_login import login_user, logout_user, current_user, login_required
from backend.stutterdetection import analyze_stutter
import os
import uuid


@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please try again.', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    progress = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.timestamp.desc()).first()
    level = progress.level if progress else 1
    score = progress.score if progress else 0

    done_ids = db.session.query(Progress.sentence_id).filter_by(
        user_id=current_user.id, status='fluent'
    ).all()
    done_ids = [id for (id,) in done_ids]
    next_sentence = Sentence.query.filter(
        Sentence.level == level,
        ~Sentence.id.in_(done_ids)
    ).first()

    return render_template(
        'dashboard.html',
        user=current_user,
        level=level,
        score=score,
        sentence=next_sentence
    )

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('welcome'))

@app.route('/upload-audio', methods=['POST'])
@login_required
def upload_audio():
    audio = request.files['audio']
    sentence_id = request.form.get("sentence_id")
    if not sentence_id:
        return jsonify({"error": "No sentence_id provided"}), 400

    audio_folder = "backend/audio"
    os.makedirs(audio_folder, exist_ok=True)
    filename = f"{current_user.username}_{uuid.uuid4().hex[:8]}.webm"
    save_path = os.path.join(audio_folder, filename)
    audio.save(save_path)

    result = analyze_stutter(save_path)
    status = 'fluent' if "You Sound Smooth" in result else 'stuttering'

    progress = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.timestamp.desc()).first()
    level = progress.level if progress else 1
    score = progress.score if progress else 0

    if status == 'fluent':
        score += 10
        if score >= 80:
            level += 1
            score = 0      # reset score for the new level

    prog = Progress(
        user_id=current_user.id,
        sentence_id=sentence_id,
        status=status,
        level=level,
        score=score
    )
    db.session.add(prog)
    db.session.commit()
    return jsonify({"result": result, "status": status, "level": level, "score": score})