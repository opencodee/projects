from flask import Flask, request, jsonify, redirect, render_template
import sqlite3
import random
import string
import threading

app = Flask(__name__)

conn = sqlite3.connect('urls.db', check_same_thread=False)
c = conn.cursor()
lock = threading.Lock()

c.execute('''CREATE TABLE IF NOT EXISTS urls
             (id INTEGER PRIMARY KEY AUTOINCREMENT, original_url TEXT, short_url TEXT)''')
conn.commit()

def generate_short_url():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form['url']
    if not original_url:
        return render_template('index.html', error='URL is required')

    isValidUrl = original_url.startswith(('http://', 'https://'))
    if not isValidUrl:
        original_url = "https://" + original_url

    lock.acquire()
    c.execute("SELECT short_url FROM urls WHERE original_url=?", (original_url,))
    existing_short_url = c.fetchone()
    lock.release()

    if existing_short_url:
        short_url = existing_short_url[0]
    else:
        short_url = generate_short_url()
        lock.acquire()
        c.execute("INSERT INTO urls (original_url, short_url) VALUES (?, ?)", (original_url, short_url))
        conn.commit()
        lock.release()

    return jsonify({'short_url': f"{request.host_url}{short_url}"}), 201

@app.route('/<short_url>')
def redirect_to_original(short_url):
    lock.acquire()
    c.execute("SELECT original_url FROM urls WHERE short_url=?", (short_url,))
    url_entry = c.fetchone()
    lock.release()
    if url_entry:
        original_url = url_entry[0]
        return redirect(original_url)
    else:
        return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)