from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
import base64

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///my_database.db"
app.secret_key = 'Mahmoud123'
app.permanent_session_lifetime = timedelta(days=6)

# Database initialization
db = SQLAlchemy(app)

# User model
class Account(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    user_password = db.Column(db.String(200), nullable=False)
    admin_status = db.Column(db.Boolean, default=False)
    books = db.relationship('Library', backref='user', lazy='select')

    def __init__(self, username, user_password, admin_status=False):
        self.username = username
        self.user_password = generate_password_hash(user_password)
        self.admin_status = admin_status

# Book model
class Library(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    cover_image = db.Column(db.LargeBinary, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('account.user_id'), nullable=True)

    def __init__(self, title, author=None, cover_image=None, owner_id=None):
        self.title = title
        self.author = author
        self.cover_image = cover_image
        self.owner_id = owner_id

# Authentication decorator
def user_login_required(view_function):
    @wraps(view_function)
    def wrapper_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first!")
            return redirect(url_for('login'))
        return view_function(*args, **kwargs)
    return wrapper_function

# Admin access decorator
def admin_access_required(view_function):
    @wraps(view_function)
    def wrapper_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first!")
            return redirect(url_for('login'))
        user = Account.query.get(session['user_id'])
        if not user or not user.admin_status:
            flash("Access denied!")
            return redirect(url_for('profile'))
        return view_function(*args, **kwargs)
    return wrapper_function

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        is_admin = 'is_admin' in request.form  
        
        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('register'))

        existing_user = Account.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for('register'))

        new_user = Account(username=username, user_password=password, admin_status=is_admin)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Account.query.filter_by(username=username).first()

        if user and check_password_hash(user.user_password, password):
            session['user_id'] = user.user_id
            flash("Login successful!")
            return redirect(url_for('profile'))
        else:
            flash("Invalid login credentials!")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!")
    return redirect(url_for('login'))

@app.route('/profile')
@user_login_required
def profile():
    user = Account.query.get(session['user_id'])
    return render_template('profile.html', user=user, books=user.books)

@app.route('/add-book', methods=['GET', 'POST'])
@user_login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        cover_image = request.files['image'].read() if 'image' in request.files else None
        
        new_book = Library(title=title, author=author, cover_image=cover_image, owner_id=session['user_id'])
        db.session.add(new_book)
        db.session.commit()
        
        flash("Book added successfully!")
        return redirect(url_for('profile'))

    return render_template('add_book.html')

@app.route('/delete-book/<int:book_id>')
@user_login_required
def delete_book(book_id):
    book = Library.query.get(book_id)
    if book and book.user.user_id == session['user_id']:
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted successfully!")
    else:
        flash("You do not have permission to delete this book!")
    return redirect(url_for('profile'))

@app.route('/admin-dashboard')
@admin_access_required
def admin_dashboard():
    users = Account.query.all()
    books = Library.query.all()
    return render_template('admin_dashboard.html', users=users, books=books)

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@admin_access_required
def edit_user(user_id):
    user = Account.query.get(user_id)
    if not user:
        flash("User not found!")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:
            user.user_password = generate_password_hash(request.form['password'])
        user.admin_status = 'is_admin' in request.form
        db.session.commit()
        flash(f"User {user.username} updated successfully!")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_user.html', user=user)

@app.route('/admin/delete-user/<int:user_id>')
@admin_access_required
def delete_user(user_id):
    user = Account.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted!")
    else:
        flash("User not found!")
    return redirect(url_for('admin_dashboard'))

@app.route('/view-books')
@user_login_required
def view_books():
    books = Library.query.all()
    return render_template('view_books.html', books=books)

# Filter for base64 encoding
@app.template_filter('b64encode')
def b64encode_filter(image):
    return base64.b64encode(image).decode('utf-8')

# Database initialization
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
