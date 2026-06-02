from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
#database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    # Posts Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()
init_db()
#หน้าแรกhome 
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""
        SELECT posts.id,
               posts.title,
               posts.content,
               users.username
        FROM posts
        JOIN users
        ON posts.user_id = users.id
        ORDER BY posts.id DESC
    """)
    posts = c.fetchall()
    conn.close()
    return render_template('index.html',
        username=session.get('username'),
        posts=posts
    )
#สมัครสมาชิก
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            flash(
                'การลงทะเบียนสำเร็จ! กรุณาเข้าสู่ระบบ',
                'success'
            )
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash(
                'ชื่อผู้ใช้นี้มีอยู่แล้ว กรุณาเลือกชื่ออื่น',
                'danger'
            )
        finally:
            conn.close()
    return render_template('register.html')
#ล็อกอิน
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('เข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('index'))
        else:
            flash(
                'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง',
                'danger'
            )
    return render_template('login.html')
#ล็อกเอาท์
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('ออกจากระบบเรียบร้อยแล้ว', 'success')
    return redirect(url_for('index'))
#สร้างโพสต์
@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        flash(
            'กรุณาเข้าสู่ระบบก่อนสร้างโพสต์',
            'danger'
        )
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO posts
            (title, content, user_id)
            VALUES (?, ?, ?)
            """,
            (
                title,
                content,
                session['user_id']
            )
        )
        conn.commit()
        conn.close()
        flash(
            'สร้างโพสต์เรียบร้อยแล้ว',
            'success'
        )
        return redirect(url_for('index'))
    return render_template('create.html')
#ลบโพสต์
@app.route('/delete/<int:post_id>')
def delete(post_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(
        """
        DELETE FROM posts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session['user_id']
        )
    )
    conn.commit()
    conn.close()
    flash('ลบโพสต์เรียบร้อยแล้ว', 'success')
    return redirect(url_for('index'))
# รันแอป
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)