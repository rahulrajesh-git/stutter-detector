from flask_app import app, db
from flask_app.models import Sentence

def seed_sentences():
    sentence1 = [
        'Hai', 'This', 'Please', 'Story', 'Welcome', 'Work', 'Idea',
        'Hello', 'Good', 'Water', 'Happy', 'Simple', 'Speak'  # 6 more → 13 total = 130 points possible
    ]
    sentence2 = [
        'This is an example for non-Stuttering',
        'Let me know your name',
        'Tomorrow is Holiday',
        'Good morning',
        'This is a sample audio to detect stuttering',
        'Mysuru is a place in Karnataka',
        'Let me know your name, you have done a great work',
        'Please speak clearly into the microphone',
        'Practice makes a man perfect',
        'I enjoy learning new things every day'
    ]

    if Sentence.query.count() == 0:
        for s in sentence1:
            db.session.add(Sentence(text=s, level=1))
        for s in sentence2:
            db.session.add(Sentence(text=s, level=2))
        db.session.commit()
        print("Sentences seeded successfully!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_sentences()
    app.run(debug=True)
