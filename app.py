from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci_rahasia_anda'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), default='user') # 'admin' or 'user'

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    artist = db.Column(db.String(150), nullable=False)

class UserPlaylist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'))
    song = db.relationship('Song')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---
@app.route('/')
def index():
    songs = Song.query.all()
    return render_template('index.html', songs=songs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        flash("Username atau Password salah!")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != 'admin':
        return "Akses Ditolak!", 403
    if request.method == 'POST':
        title = request.form.get('title')
        artist = request.form.get('artist')
        new_song = Song(title=title, artist=artist)
        db.session.add(new_song)
        db.session.commit()
        flash("Lagu berhasil ditambahkan!")
    return render_template('admin.html')

@app.route('/add_to_playlist/<int:song_id>')
@login_required
def add_to_playlist(song_id):
    new_entry = UserPlaylist(user_id=current_user.id, song_id=song_id)
    db.session.add(new_entry)
    db.session.commit()
    flash("Ditambahkan ke playlist!")
    return redirect(url_for('index'))

@app.route('/my_playlist')
@login_required
def my_playlist():
    playlist = UserPlaylist.query.filter_by(user_id=current_user.id).all()
    return render_template('playlist.html', playlist=playlist)

@app.route('/remove/<int:entry_id>')
@login_required
def remove_from_playlist(entry_id):
    entry = UserPlaylist.query.get(entry_id)
    if entry and entry.user_id == current_user.id:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('my_playlist'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='boss').first():
            db.session.add(User(username='boss', password='123', role='admin'))
            db.session.add(User(username='student', password='123', role='user'))
            db.session.commit()
    app.run(debug=True)