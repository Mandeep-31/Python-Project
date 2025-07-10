from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edumate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'EduMateSecretKey'
db = SQLAlchemy(app)
# === Models ===
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    link = db.Column(db.String(200))
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
    
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date)

class ExamQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    year = db.Column(db.Integer)
    question_text = db.Column(db.Text)
class PastQuestionPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    link = db.Column(db.String(300))
# === Routes ===
@app.route('/')
def home():
    goals = Goal.query.order_by(Goal.due_date).all()
    return render_template('dashboard.html', goals=goals)

@app.route('/resources') 
def view_resources():
    resources = Resource.query.order_by(Resource.added_on.desc()).all()
    return render_template('view_resources.html', resources=resources)

@app.route('/add-resource-form')
def add_resource_form():
    return render_template('add_resource.html')

@app.route('/add-resource', methods=['POST'])
def add_resource():
    title = request.form['title']
    type_ = request.form['type']
    link = request.form['link']
    resource = Resource(title=title, type=type_, link=link)
    db.session.add(resource)
    db.session.commit()
    return redirect(url_for('view_resources'))
@app.route('/add-goal', methods=['POST'])
def add_goal():
    desc = request.form['description']
    due = request.form['due_date']
    goal = Goal(description=desc, due_date=datetime.strptime(due, '%Y-%m-%d'))
    db.session.add(goal)
    db.session.commit()
    return redirect(url_for('home'))
@app.route('/toggle-goal/<int:goal_id>')
def toggle_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    goal.is_done = not goal.is_done
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/exam-questions')
def exam_questions():
    questions = ExamQuestion.query.order_by(ExamQuestion.year.desc()).all()
    return render_template('questions.html', questions=questions)

@app.route('/add-question', methods=['POST'])
def add_question():
    subject = request.form['subject']
    unit = request.form['unit']
    year = int(request.form['year'])
    question_text = request.form['question_text']
    q = ExamQuestion(subject=subject, unit=unit, year=year, question_text=question_text)
    db.session.add(q)
    db.session.commit()
    return redirect(url_for('exam_questions'))

@app.route('/past-papers')
def past_papers():
    papers = PastQuestionPDF.query.order_by(PastQuestionPDF.year.desc()).all()
    return render_template('past_papers.html', papers=papers)

@app.route('/add-paper', methods=['POST'])
def add_paper():
    title = request.form['title']
    year = int(request.form['year'])
    link = request.form['link']
    paper = PastQuestionPDF(title=title, year=year, link=link)
    db.session.add(paper)
    db.session.commit()
    return redirect(url_for('past_papers'))

@app.route('/delete-paper/<int:paper_id>', methods=['POST'])
def delete_paper(paper_id):
    paper = PastQuestionPDF.query.get_or_404(paper_id)
    db.session.delete(paper)
    db.session.commit()
    return redirect(url_for('past_papers'))
# === Run ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
