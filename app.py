from flask import Flask, request, render_template_string, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database setup
conn = sqlite3.connect('cloud_storage.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        cloud_name TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
conn.commit()
conn.close()

# HTML Templates
login_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; background-color: #333; position: relative; }
        form { margin: 20px; }
        input, button { margin: 10px 0; }
        .branding {
            font-size: 3rem;
            font-weight: bold;
            text-shadow: 2px 2px 4px #000;
            color: #f39c12;
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
        }
        .dynamic-bg { position: absolute; width: 100%; height: 100%; top: 0; left: 0; z-index: -1; transition: background-color 1s; }
        @media (max-width: 768px) { button, input { font-size: 18px; } }
    </style>
</head>
<body>
    <div class="branding">CloudSpark</div>
    <div class="dynamic-bg" id="bg"></div>
    <div>
        <h2>Login</h2>
        <form action="/login" method="post">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <a href="/register">Create an Account</a>
    </div>
    <script>
        function changeBackgroundColor() {
            const r = Math.floor(Math.random() * 256);
            const g = Math.floor(Math.random() * 256);
            const b = Math.floor(Math.random() * 256);
            const rgbColor = `rgb(${r}, ${g}, ${b})`;

            document.getElementById('bg').style.backgroundColor = rgbColor;
            const textColor = (r * 0.299 + g * 0.587 + b * 0.114) > 186 ? 'black' : 'white';
            document.body.style.color = textColor;
            document.querySelectorAll('button, a').forEach(el => {
                el.style.color = textColor;
                el.style.backgroundColor = rgbColor;
            });
        }

        changeBackgroundColor();
        setInterval(changeBackgroundColor, 5000);
    </script>
</body>
</html>
'''

register_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; background-color: #333; position: relative; }
        form { margin: 20px; }
        input, button { margin: 10px 0; }
        .branding {
            font-size: 3rem;
            font-weight: bold;
            text-shadow: 2px 2px 4px #000;
            color: #f39c12;
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
        }
        .dynamic-bg { position: absolute; width: 100%; height: 100%; top: 0; left: 0; z-index: -1; transition: background-color 1s; }
        @media (max-width: 768px) { button, input { font-size: 18px; } }
    </style>
</head>
<body>
    <div class="branding">CloudSpark</div>
    <div class="dynamic-bg" id="bg"></div>
    <div>
        <h2>Register</h2>
        <form action="/register" method="post">
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
        <a href="/">Back to Login</a>
    </div>
    <script>
        function changeBackgroundColor() {
            const r = Math.floor(Math.random() * 256);
            const g = Math.floor(Math.random() * 256);
            const b = Math.floor(Math.random() * 256);
            const rgbColor = `rgb(${r}, ${g}, ${b})`;

            document.getElementById('bg').style.backgroundColor = rgbColor;
            const textColor = (r * 0.299 + g * 0.587 + b * 0.114) > 186 ? 'black' : 'white';
            document.body.style.color = textColor;
            document.querySelectorAll('button, a').forEach(el => {
                el.style.color = textColor;
                el.style.backgroundColor = rgbColor;
            });
        }

        changeBackgroundColor();
        setInterval(changeBackgroundColor, 5000);
    </script>
</body>
</html>
'''

cloud_storage_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Storage</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            height: 100vh;
            overflow: hidden;
            font-family: Arial, sans-serif;
            color: white;
            text-align: center;
            position: relative;
            background-color: #333;
        }

        .container {
            padding: 20px;
            z-index: 1;
            position: relative;
            margin-top: 80px;  /* Adjust to avoid overlap with branding */
        }

        .branding {
            font-size: 4rem;
            font-weight: bold;
            position: absolute;
            top: 20px;
            left: 20px;  /* Branding on the top left corner */
            text-shadow: 2px 2px 4px #000;
            color: #f39c12;
        }

        h2, h3 {
            margin: 20px 0;
        }

        form {
            margin: 20px 0;
        }

        input[type="file"], button {
            font-size: 16px;
            margin: 10px;
        }

        button {
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }

        button:hover {
            opacity: 0.8;
        }

        .dynamic-bg {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: -1;
            transition: background-color 1s;
        }

        @media (max-width: 768px) {
            button, input {
                font-size: 18px;
            }
        }
    </style>
</head>
<body>
    <div class="dynamic-bg" id="bg"></div>
    <div class="branding">CloudSpark</div>
    <div class="container">
        <h2>Welcome to Your Cloud Storage, {{ name }}</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit">Upload</button>
        </form>
        <h3>Your Files</h3>
        <ul>
            {% for file in files %}
                <li>{{ file }}
                    <a href="/download/{{ file }}">Download</a> | 
                    <a href="/delete/{{ file }}">Delete</a>
                </li>
            {% endfor %}
        </ul>
        <a href="/logout">Logout</a>
    </div>
    <script>
        function changeBackgroundColor() {
            const r = Math.floor(Math.random() * 256);
            const g = Math.floor(Math.random() * 256);
            const b = Math.floor(Math.random() * 256);
            const rgbColor = `rgb(${r}, ${g}, ${b})`;

            document.getElementById('bg').style.backgroundColor = rgbColor;
            const textColor = (r * 0.299 + g * 0.587 + b * 0.114) > 186 ? 'black' : 'white';
            document.body.style.color = textColor;
            document.querySelectorAll('button, a').forEach(el => {
                el.style.color = textColor;
                el.style.backgroundColor = rgbColor;
            });
        }

        changeBackgroundColor();
        setInterval(changeBackgroundColor, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def login():
    return render_template_string(login_html)

@app.route('/login', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']
    conn = sqlite3.connect('cloud_storage.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, password, name FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        session['name'] = user[2]
        return redirect(url_for('cloud_storage'))
    flash('Invalid credentials')
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template_string(register_html)

@app.route('/register', methods=['POST'])
def register_user():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    hashed_password = generate_password_hash(password)
    conn = sqlite3.connect('cloud_storage.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        flash('Email already registered')
        conn.close()
        return redirect(url_for('register'))
    conn.close()
    return redirect(url_for('login'))

@app.route('/cloud_storage')
def cloud_storage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('cloud_storage.db')
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM user_files WHERE user_id = ?', (session['user_id'],))
    files = cursor.fetchall()
    conn.close()
    
    return render_template_string(cloud_storage_html, name=session['name'], files=[file[0] for file in files])

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('cloud_storage'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('cloud_storage'))
    
    filename = file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = sqlite3.connect('cloud_storage.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_files (user_id, filename) VALUES (?, ?)', (session['user_id'], filename))
    conn.commit()
    conn.close()
    
    return redirect(url_for('cloud_storage'))

@app.route('/download/<filename>')
def download_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>')
def delete_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = sqlite3.connect('cloud_storage.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_files WHERE user_id = ? AND filename = ?', (session['user_id'], filename))
    conn.commit()
    conn.close()
    
    return redirect(url_for('cloud_storage'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('name', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
