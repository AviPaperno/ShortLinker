# Подключаем основные библиотеки
from flask import Flask, g, render_template, session, redirect
import sqlite3

# Подключаем библотеку flask-wtf
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

# Подключаем библиотеки необходимые для генерации ссылки
import random
import string

# Подключим библиотеку для проверки
import re, urllib

# Создаём приложение
app = Flask(__name__)

# Добавляем в файл конфигурации SECRET_KEY, необходимо для нормальной работы Flask-WTF
app.config['SECRET_KEY'] = "Don't Panic! 42!"

# Название файла БД
DATABASE = 'ShortURL.db'


class LinkForm(FlaskForm):
    '''
    Класс - форма для ввода длинной ссылки
    '''
    name = StringField("Введите длинную ссылку", validators=[DataRequired()])
    submit = SubmitField('ОК')


# Следующие две функции необходимы для работы с БД
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Функция - запрос в БД. В случае необходимости, может закомитить информацию
def query_db(query, args=(), one=False, commit=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if commit:
        get_db().commit()
    return (rv[0] if rv else None) if one else rv


# Создаёт короткую ссылку, пытается вставить в БД, при возникновении ошибки,
# вызванной повторным ключом, перезапускается
def generate_short_link(long_link):
    while True:
        try:
            short_link = "".join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in
                                 range(random.randrange(5, 8)))
            query_db('INSERT INTO links(local_addres,real_addres) VALUES (?, ?)', args=(short_link, long_link),
                     commit=True)
            return short_link
        except:
            pass


# Заглавная страница
# Здесь пользователь вводит URL, который сразу дополняется,
# при необходимости, до полный и проходит проверку с помощью
# регулярного выражения. Затем добавляется информация в БД и пользователь
# получает страницу с сокращённой ссылкой
@app.route('/', methods=["GET", "POST"])
def que():
    link_input = LinkForm()
    if link_input.validate_on_submit():
        tmp = link_input.name.data
        if tmp.find("http://") != 0 and tmp.find("https://") != 0:
            tmp = "http://" + tmp
        session['long_link'] = tmp
        if re.match(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tmp):
            session['short_link'] = generate_short_link(session.get('long_link'))
            return render_template('index2.html', short_link=session.get('short_link'))
        else:
            return render_template('index3.html')
    return render_template('index.html', form=link_input)


# При переходе по адресу, эта функция проверяет, есть ли такой короткий адрес в БД.
# Если есть - выполняется переход по ссылке.
@app.route('/<short_link>')
def short_link_redirect(short_link):
    try:
        tmp = query_db('SELECT real_addres FROM links WHERE local_addres =?', args=(short_link,))[0][0]
        return redirect(tmp)
    except:
        return render_template('index3.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
