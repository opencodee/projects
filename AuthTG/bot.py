from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import time
import hashlib
import os
import telebot
from telebot import types
from pyzbar.pyzbar import decode
from PIL import Image
import threading

app = Flask(__name__)
app.secret_key = os.urandom(24)
bot = telebot.TeleBot('TOKEN')

DATABASE = 'database.db'
HASH_EXPIRATION_TIME = 60  # seconds

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            chat_id INTEGER PRIMARY KEY,
                            first_name TEXT,
                            last_name TEXT,
                            username TEXT,
                            hash TEXT UNIQUE,
                            timestamp INTEGER,
                            auth_status TEXT
                          )''')
        conn.commit()

@app.route('/')
def index():
    if 'user' in session:
        user = session['user']
        return render_template('profile.html', user=user)
    return render_template('index.html')

@app.route('/get_hash', methods=['GET'])
def get_hash():
    hash_value = hashlib.sha256(os.urandom(64)).hexdigest()
    timestamp = int(time.time())
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (hash, timestamp, auth_status) VALUES (?, ?, ?)", (hash_value, timestamp, 'pending'))
        conn.commit()
    return jsonify({'hash': hash_value})

@app.route('/check_auth_status', methods=['GET'])
def check_auth_status():
    hash_value = request.args.get('hash')
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE hash = ?", (hash_value,))
        user = cursor.fetchone()
    if user:
        timestamp = int(user[5])
        if user[6] == 'success':
            session['user'] = {
                'chat_id': user[0],
                'first_name': user[1],
                'last_name': user[2],
                'username': user[3]
            }
            return jsonify({'status': 'success'})
        elif int(time.time()) - timestamp > HASH_EXPIRATION_TIME:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE hash = ?", (hash_value,))
                conn.commit()
            return jsonify({'status': 'error', 'message': 'Время истекло', 'regenerate': True})
    return jsonify({'status': 'pending'})

@app.route('/regenerate_hash', methods=['POST'])
def regenerate_hash():
    hash_value = hashlib.sha256(os.urandom(64)).hexdigest()
    timestamp = int(time.time())
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (hash, timestamp, auth_status) VALUES (?, ?, ?)", (hash_value, timestamp, 'pending'))
        conn.commit()
    return jsonify({'hash': hash_value})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Привет! Отправьте мне фото QR кода или последние несколько символов хеша.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)
    
    with open("received_qr.png", 'wb') as new_file:
        new_file.write(downloaded_file)
    
    try:
        decoded_qr = decode(Image.open("received_qr.png"))
        if decoded_qr:
            hash_value = decoded_qr[0].data.decode('utf-8')
            handle_hash(message, hash_value)
        else:
            bot.send_message(chat_id, "Не удалось распознать QR код.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при обработке QR кода: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    hash_value = message.text.strip()
    if len(hash_value) >= 6:  # <= 6 characters long
        handle_hash(message, hash_value)
    else:
        bot.send_message(chat_id, "Хеш должен содержать минимум 6 символов.")

def handle_hash(message, hash_value):
    chat_id = message.chat.id
    first_name = message.chat.first_name
    last_name = message.chat.last_name
    username = message.chat.username

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE hash LIKE ?", (f"%{hash_value}",))
        user = cursor.fetchone()
        if user:
            timestamp = int(user[5])
            if int(time.time()) - timestamp > HASH_EXPIRATION_TIME:
                bot.send_message(chat_id, "Время истекло. Попробуйте снова.")
            else:
                cursor.execute("""
                    UPDATE users 
                    SET chat_id = ?, first_name = ?, last_name = ?, username = ?, auth_status = ? 
                    WHERE hash = ?
                """, (chat_id, first_name, last_name, username, 'success', user[4]))
                conn.commit()
                bot.send_message(chat_id, "Успешная авторизация!")
        else:
            bot.send_message(chat_id, "Неверный QR код или хеш.")

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def run_telebot():
    bot.polling()

if __name__ == "__main__":
    init_db()

    flask_thread = threading.Thread(target=run_flask)
    telebot_thread = threading.Thread(target=run_telebot)
    
    flask_thread.start()
    telebot_thread.start()
    
    flask_thread.join()
    telebot_thread.join()