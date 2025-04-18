from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'vulnerable_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['is_admin'] = True if user['username'] == 'admin' else False
            return redirect('/profile')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    user = conn.execute("SELECT username, email FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    posts = conn.execute("SELECT content FROM posts WHERE user_id = ?", (session['user_id'],)).fetchall()
    conn.close()
    return render_template('profile.html', user=user, posts=posts)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            conn = get_db_connection()
            conn.execute('INSERT INTO uploads (user_id, filename) VALUES (?, ?)', (session['user_id'], filename))
            conn.commit()
            conn.close()

            return redirect(url_for('gallery'))

    return render_template('upload.html')

@app.route('/gallery')
def gallery():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if session.get('is_admin'):
        files = conn.execute('SELECT filename, user_id FROM uploads').fetchall()
    else:
        files = conn.execute('SELECT filename FROM uploads WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()

    return render_template('gallery.html', files=files)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

        if user['password'] == old_password:
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, session['user_id']))
            conn.commit()
        conn.close()

        return redirect(url_for('profile'))

    return render_template('change_password.html')

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']

        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user_id, content) VALUES (?, ?)', (session['user_id'], content))
        conn.commit()
        conn.close()

        return redirect(url_for('posts'))

    return render_template('create_post.html')

@app.route('/posts')
def posts():
    conn = get_db_connection()
    if session.get('is_admin'):
        posts = conn.execute('SELECT posts.content, users.username FROM posts JOIN users ON posts.user_id = users.id').fetchall()
    else:
        posts = conn.execute('SELECT content, username FROM posts JOIN users ON posts.user_id = users.id WHERE users.id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('posts.html', posts=posts)



@app.route('/view_posts')
def view_posts():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    posts = conn.execute('SELECT posts.content, users.username FROM posts JOIN users ON posts.user_id = users.id').fetchall()
    conn.close()
    return render_template('view_posts.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)

