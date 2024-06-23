from flask import Flask, render_template, request, make_response, request, jsonify
from flask import redirect, url_for, flash
import uuid
import random
import sqlite3
import json
import os
import threading

app = Flask(__name__)
app.secret_key = '1234567890'

DB_PATH = 'static/site.db'

@app.route('/')
def index():
    products = get_products_from_database()
    return render_template('index.html', products=products)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/thank-you')
def thank_you_page():
    return render_template('thank-you.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.json
        product_id = data['product_id']
        customer_id = data['customer_id']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cart (product_id, customer_id) VALUES (?, ?)", (product_id, customer_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/get_cart_items', methods=['GET'])
def get_cart_items():
    try:
        customer_id = request.args.get('customer_id')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT products.id, products.name, products.price, products.image FROM cart JOIN products ON cart.product_id = products.id WHERE cart.customer_id = ?", (customer_id,))
        cart_items = cursor.fetchall()

        conn.commit()
        conn.close()

        items = [{'id': item[0], 'name': item[1], 'price': item[2], 'image': item[3]} for item in cart_items]

        return jsonify(items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/delete_cart_item', methods=['DELETE'])
def delete_cart_item():
    try:
        customer_id = request.args.get('customer_id')
        product_id = request.args.get('product_id')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM cart WHERE customer_id = ? AND product_id = ?", (customer_id, product_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Cart item deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def clear_cart(customer_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM cart WHERE customer_id = ?", (customer_id,))
        conn.commit()

        conn.close()
    except Exception as e:
        print("Error clearing cart:", e)

def get_products_from_database():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.commit()
    conn.close()
    return products

def get_valid_key():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key FROM keys WHERE id = 1')
        result = cursor.fetchone()
        return result[0] if result else None

@app.route('/check_key', methods=['POST'])
def check_key():
    data = request.get_json()
    key = data.get('key')
    valid_key = get_valid_key()
    if key == valid_key:
        return jsonify({'status': 'success', 'message': 'Ключ верный!'})
    else:
        return jsonify({'status': 'error', 'message': 'Ключ неверный!'})

@app.route('/submit_order', methods=['POST'])
def submit_order():
    data = request.get_json()

    customer_id = data.get('customerID')
    product_ids = data.get('productIDs')
    total_items = data.get('totalItems')
    total_price = data.get('totalPrice')

    if not customer_id:
        return jsonify({'status': 'error', 'message': 'Отсутствует customerID'}), 400
    if not product_ids:
        return jsonify({'status': 'error', 'message': 'Отсутствует productIDs'}), 400
    if not total_items:
        return jsonify({'status': 'error', 'message': 'Отсутствует totalItems'}), 400
    if not total_price:
        return jsonify({'status': 'error', 'message': 'Отсутствует totalPrice'}), 400

    try:
        send_new_order_notification(customer_id, product_ids, total_items, total_price)
        clear_cart(customer_id)

        return jsonify({'status': 'success', 'message': 'Заказ успешно оформлен!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Произошла ошибка: {str(e)}'}), 500

#Telegram BOT
import telebot
from telebot import types
import sqlite3
import os

API_TOKEN = 'BOT_TOKEN'
CHAT_ID = 'CHAT_ID_COOKIER'
bot = telebot.TeleBot(API_TOKEN)

user_data = {}

def save_product(data):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO products (name, price, image, visibility) VALUES (?, ?, ?, ?)
        ''', (data['name'], data['price'], data['image'], data['visibility']))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при сохранении продукта: {e}")
    finally:
        conn.close()

def update_product_field(product_id, field, value):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'''
        UPDATE products SET {field} = ? WHERE id = ?
        ''', (value, product_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении продукта: {e}")
    finally:
        conn.close()

def get_all_products():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, visibility FROM products')
        products = cursor.fetchall()
        return products
    except Exception as e:
        print(f"Ошибка при получении списка продуктов: {e}")
        return []
    finally:
        conn.close()

def get_product_details(product_ids):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        placeholders = ', '.join(['?'] * len(product_ids.split(',')))
        cursor.execute(f'SELECT id, name, price, image FROM products WHERE id IN ({placeholders})', product_ids.split(','))
        products = cursor.fetchall()
        return products
    except Exception as e:
        print(f"Ошибка при получении деталей продукта: {e}")
        return []
    finally:
        conn.close()

def get_product_by_id(product_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, price, image, visibility FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        return product
    except Exception as e:
        print(f"Ошибка при получении данных товара: {e}")
        return None
    finally:
        conn.close()

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "/addproduct - Добавить новый товар. Бот запросит название, цену, изображение и доступность.\n"
        "/changevisibility - Изменить видимость товара. Бот запросит ID товара и новую видимость (yes/no).\n"
        "/listproducts - Показать список всех товаров с их ID, названием и видимостью.\n"
        "/updateproduct - Обновить данные товара. Бот запросит ID товара и предложит обновить имя, цену, изображение или видимость.\n"
        "/viewproduct - будет предоставлять пользователю информацию о товаре по его ID в одном сообщении вместе с изображением.\n"
        "/setkey - Обновить ключ безопасности. Бот запросит новый ключ, и в целях конфиденциальности удалит его.\n"
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['addproduct'])
def start_add_product(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "Введите название товара:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    bot.send_message(chat_id, "Введите цену товара:")
    bot.register_next_step_handler(message, get_price)

def get_price(message):
    chat_id = message.chat.id
    try:
        price = float(message.text)
        user_data[chat_id]['price'] = price
        bot.send_message(chat_id, "Отправьте картинку товара:")
        bot.register_next_step_handler(message, get_image)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите правильное число для цены.")
        bot.register_next_step_handler(message, get_price)

def get_image(message):
    chat_id = message.chat.id
    if message.content_type == 'photo':
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            if not os.path.exists('static/img'):
                os.makedirs('static/img')

            unique_filename_file = str(uuid.uuid4()) + os.path.splitext(file_info.file_path)[-1]
            unique_filename = f"static/img/{unique_filename_file}"
            with open(unique_filename, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            user_data[chat_id]['image'] = unique_filename
            bot.send_message(chat_id, "Выберите доступность товара (введите 'yes' или 'no'):")
            bot.register_next_step_handler(message, get_visibility)
        except Exception as e:
            bot.send_message(chat_id, "Ошибка при обработке изображения. Попробуйте еще раз.")
            print(f"Ошибка при обработке изображения: {e}")
            bot.register_next_step_handler(message, get_image)
    else:
        bot.send_message(chat_id, "Пожалуйста, отправьте изображение.")
        bot.register_next_step_handler(message, get_image)


def get_visibility(message):
    chat_id = message.chat.id
    visibility = message.text.lower()
    if visibility in ['yes', 'no']:
        user_data[chat_id]['visibility'] = visibility
        try:
            save_product(user_data[chat_id])
            bot.send_message(chat_id, "Товар успешно добавлен!")
        except Exception as e:
            bot.send_message(chat_id, "Ошибка при сохранении товара. Попробуйте еще раз.")
            print(f"Ошибка при сохранении товара: {e}")
        finally:
            user_data.pop(chat_id)
    else:
        bot.send_message(chat_id, "Пожалуйста, введите 'yes' или 'no' для доступности.")
        bot.register_next_step_handler(message, get_visibility)

@bot.message_handler(commands=['changevisibility'])
def start_change_visibility(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    products = get_all_products()
    if not products:
        bot.send_message(chat_id, "В базе данных нет товаров.")
        return
    
    product_list = "\n".join([f"ID: {product[0]}, Название: {product[1]}, Видимость: {product[2]}" for product in products])
    bot.send_message(chat_id, f"Вот список товаров:\n{product_list}\nВведите ID товара, для которого вы хотите изменить видимость:")
    bot.register_next_step_handler(message, get_product_id)

def get_product_id(message):
    chat_id = message.chat.id
    try:
        product_id = int(message.text)
        user_data[chat_id]['product_id'] = product_id
        bot.send_message(chat_id, "Введите новую видимость для товара (введите 'yes' или 'no'):")
        bot.register_next_step_handler(message, get_new_visibility)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите правильное число для ID товара.")
        bot.register_next_step_handler(message, get_product_id)

def get_new_visibility(message):
    chat_id = message.chat.id
    visibility = message.text.lower()
    if visibility in ['yes', 'no']:
        product_id = user_data[chat_id]['product_id']
        try:
            update_product_field(product_id, 'visibility', visibility)
            bot.send_message(chat_id, f"Видимость товара с ID {product_id} успешно обновлена на '{visibility}'!")
        except Exception as e:
            bot.send_message(chat_id, "Ошибка при обновлении видимости. Попробуйте еще раз.")
            print(f"Ошибка при обновлении видимости: {e}")
        finally:
            user_data.pop(chat_id)
    else:
        bot.send_message(chat_id, "Пожалуйста, введите 'yes' или 'no' для видимости.")
        bot.register_next_step_handler(message, get_new_visibility)

@bot.message_handler(commands=['listproducts'])
def list_products(message):
    chat_id = message.chat.id
    products = get_all_products()
    if not products:
        bot.send_message(chat_id, "В базе данных нет товаров.")
        return

    product_list = "\n".join([f"ID: {product[0]}, Название: {product[1]}, Видимость: {product[2]}" for product in products])
    bot.send_message(chat_id, f"Вот список товаров:\n{product_list}")

@bot.message_handler(commands=['updateproduct'])
def start_update_product(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    products = get_all_products()
    if not products:
        bot.send_message(chat_id, "В базе данных нет товаров.")
        return

    product_list = "\n".join([f"ID: {product[0]}, Название: {product[1]}, Видимость: {product[2]}" for product in products])
    bot.send_message(chat_id, f"Вот список товаров:\n{product_list}\nВведите ID товара, который вы хотите обновить:")
    bot.register_next_step_handler(message, select_product_to_update)

def select_product_to_update(message):
    chat_id = message.chat.id
    try:
        product_id = int(message.text)
        user_data[chat_id]['product_id'] = product_id
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Обновить имя", callback_data="update_name"))
        markup.add(types.InlineKeyboardButton("Обновить цену", callback_data="update_price"))
        markup.add(types.InlineKeyboardButton("Обновить картинку", callback_data="update_image"))
        markup.add(types.InlineKeyboardButton("Обновить видимость", callback_data="update_visibility"))
        bot.send_message(chat_id, "Выберите, что вы хотите обновить:", reply_markup=markup)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите правильное число для ID товара.")
        bot.register_next_step_handler(message, select_product_to_update)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "update_name":
        bot.send_message(chat_id, "Введите новое имя товара:")
        bot.register_next_step_handler(call.message, update_name)
    elif call.data == "update_price":
        bot.send_message(chat_id, "Введите новую цену товара:")
        bot.register_next_step_handler(call.message, update_price)
    elif call.data == "update_image":
        bot.send_message(chat_id, "Отправьте новое изображение товара:")
        bot.register_next_step_handler(call.message, update_image)
    elif call.data == "update_visibility":
        bot.send_message(chat_id, "Введите новую видимость товара (yes/no):")
        bot.register_next_step_handler(call.message, update_visibility)

def update_name(message):
    chat_id = message.chat.id
    product_id = user_data[chat_id]['product_id']
    new_name = message.text
    try:
        update_product_field(product_id, 'name', new_name)
        bot.send_message(chat_id, f"Имя товара с ID {product_id} успешно обновлено!")
    except Exception as e:
        bot.send_message(chat_id, "Ошибка при обновлении имени товара. Попробуйте еще раз.")
        print(f"Ошибка при обновлении имени товара: {e}")

def update_price(message):
    chat_id = message.chat.id
    product_id = user_data[chat_id]['product_id']
    try:
        new_price = float(message.text)
        update_product_field(product_id, 'price', new_price)
        bot.send_message(chat_id, f"Цена товара с ID {product_id} успешно обновлена!")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите правильное число для новой цены.")
        bot.register_next_step_handler(message, update_price)
    except Exception as e:
        bot.send_message(chat_id, "Ошибка при обновлении цены товара. Попробуйте еще раз.")
        print(f"Ошибка при обновлении цены товара: {e}")

def update_image(message):
    chat_id = message.chat.id
    if message.content_type == 'photo':
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            if not os.path.exists('static/img'):
                os.makedirs('static/img')

            unique_filename_file = str(uuid.uuid4()) + os.path.splitext(file_info.file_path)[-1]
            unique_filename = f"static/img/{unique_filename_file}"
            with open(unique_filename, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            product_id = user_data[chat_id]['product_id']
            update_product_field(product_id, 'image', unique_filename)
            bot.send_message(chat_id, f"Картинка товара с ID {product_id} успешно обновлена!")
        except Exception as e:
            bot.send_message(chat_id, "Ошибка при обработке изображения. Попробуйте еще раз.")
            print(f"Ошибка при обработке изображения: {e}")
            bot.register_next_step_handler(message, update_image)
    else:
        bot.send_message(chat_id, "Пожалуйста, отправьте изображение.")
        bot.register_next_step_handler(message, update_image)

def update_visibility(message):
    chat_id = message.chat.id
    visibility = message.text.lower()
    if visibility in ['yes', 'no']:
        product_id = user_data[chat_id]['product_id']
        try:
            update_product_field(product_id, 'visibility', visibility)
            bot.send_message(chat_id, f"Видимость товара с ID {product_id} успешно обновлена на '{visibility}'!")
        except Exception as e:
            bot.send_message(chat_id, "Ошибка при обновлении видимости. Попробуйте еще раз.")
            print(f"Ошибка при обновлении видимости: {e}")
    else:
        bot.send_message(chat_id, "Пожалуйста, введите 'yes' или 'no' для видимости.")
        bot.register_next_step_handler(message, update_visibility)

def send_new_order_notification(customer_id, product_ids, total_items, total_price):
    products = get_product_details(product_ids)
    
    message = (f"Новый заказ!\n"
               f"ID клиента: {customer_id}\n"
               f"Товары:\n")
    
    for product in products:
        product_id, name, price, _ = product
        message += f"ID: {product_id}, Название: {name}, Цена: {price}\n"
    
    message += (f"Всего товаров: {total_items}\n"
                f"Общая цена: {total_price}")

    try:
        bot.send_message(CHAT_ID, message)
    except Exception as e:
        print(f"Ошибка при отправке сообщения о новом заказе: {e}")

@bot.message_handler(commands=['viewproduct'])
def start_view_product(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите ID товара, который вы хотите посмотреть:")
    bot.register_next_step_handler(message, view_product_details)

def view_product_details(message):
    chat_id = message.chat.id
    try:
        product_id = int(message.text)
        product = get_product_by_id(product_id)
        if product:
            product_id, name, price, image, visibility = product
            product_message = (f"ID: {product_id}\n"
                               f"Название: {name}\n"
                               f"Цена: {price}\n"
                               f"Доступность: {visibility}")
            if os.path.exists(image):
                with open(image, 'rb') as img:
                    bot.send_photo(chat_id, img, caption=product_message)
            else:
                bot.send_message(chat_id, product_message)
        else:
            bot.send_message(chat_id, "Товар с указанным ID не найден.")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите правильное число для ID товара.")
        bot.register_next_step_handler(message, view_product_details)
    except Exception as e:
        bot.send_message(chat_id, "Произошла ошибка при получении информации о товаре. Попробуйте еще раз.")
        print(f"Ошибка при просмотре товара: {e}")

def set_valid_key(new_key):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE keys SET key = ? WHERE id = 1', (new_key,))
        conn.commit()

@bot.message_handler(commands=['setkey'])
def request_key(message):
    msg = bot.reply_to(message, 'Введите новый ключ:')
    bot.register_next_step_handler(msg, process_key_step)

def process_key_step(message):
    try:
        new_key = message.text
        set_valid_key(new_key)
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, 'Новый ключ успешно сохранен.')
    except Exception as e:
        bot.send_message(message.chat.id, 'Произошла ошибка при сохранении ключа.')

# Запуск Flask сервера
def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Запуск Telebot
def run_telebot():
    bot.polling()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    telebot_thread = threading.Thread(target=run_telebot)
    
    flask_thread.start()
    telebot_thread.start()
    
    flask_thread.join()
    telebot_thread.join()