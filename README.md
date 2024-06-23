# Personal library of full-fledged services | Бэкенд + Фронтенд (полноценные сервисы)
1. [URL Shortener](https://github.com/opencodee/projects/tree/main/URL%20Shortener) - Сокращение ссылок.
2. [Home Restaurant](https://github.com/opencodee/projects/tree/main/Home%20Restaurant) - Сайт ресторана. Случайно увидел [такой пост](https://x.com/spasiblya/status/1791848703428292730) и просто решил повторить :)<br>
Сайт работает только в режиме чтения, добавлять блюда через него нельзя. Для этого был написан код для Телеграм бота. Отправляем боту команду ```/addproduct``` указываем название блюда, цену, фото и указываем видимость: ```yes``` или ```no```.
Так же у бота есть еще несколько команд:
> ```/addproduct``` - Добавить новый товар. Бот запросит название, цену, изображение и доступность.<br>```/changevisibility``` - Изменить видимость товара. Бот запросит ID товара и новую видимость (yes/no).<br>```/listproducts``` - Показать список всех товаров с их ID, названием и видимостью.<br>```/updateproduct``` - Обновить данные товара. Бот запросит ID товара и предложит обновить имя, цену, изображение или видимость.<br>```/viewproduct``` - будет предоставлять пользователю информацию о товаре по его ID в одном сообщении вместе с изображением.<br>```/setkey``` - Обновить ключ безопасности. Бот запросит новый ключ, и в целях конфиденциальности удалит его.

Все эти команды доступны по ```/help```.<br>
Чтобы выполнить заказ нужно набрать в корзину товаров, и на странице корзины ввести пароль для заказа.<br>
Для запуска требуется указать токен бота (```API_TOKEN```), ```CHAT_ID``` того, кому будут приходить уведомления о заказах, и секретный ключ для штфрования сессий (```app.secret_key```)<br>
<br>3. [AuthTG](https://github.com/opencodee/projects/tree/main/AuthTG) - Альтернативный способ входа пользователя на сайт при помощи бота в Телеграм.<br> Для настройки также нужно указать токен бота ```bot = telebot.TeleBot('TOKEN')``` и ключ для шифрования сессий ```app.secret_key```<br>
Пользователь нажимает на кнопку "Войти" и на странице генерируется уникальный QR код. 
![Главная страница QR](https://github.com/opencodee/projects/blob/main/AuthTG/preview.png) Для авторизации нужно отправить боту этот QR или последние 6 символов хеша, которые отображаются ниже на старнцие. QR код действует 60 секунд, после чего будет автоматически сгенерирован новый.<br>
![Страница после успешной авторизации](https://github.com/opencodee/projects/blob/main/AuthTG/preview-result.png)Если авторизация прошла успешно, то на странице отобразитья "Успешная авторизация" и произойдет автоматический переход на страницу профил.
![Запись в базе данных](https://github.com/opencodee/projects/blob/main/AuthTG/record-db.png)
Данные будут указаны те, которые были получены из профиля пользователя в Телеграм.