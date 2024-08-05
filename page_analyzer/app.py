import psycopg2
import os
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url as validate_url

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


def create_table():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            with open('page_analyzer/database.sql', 'r') as f:
                cursor.execute(f.read())
                conn.commit()


def add_to_database(url):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT (name) FROM urls")

            sites = [site[0] for site in cursor.fetchall()]
            if url not in sites:
                cursor.execute("""
                                    INSERT INTO urls (name) VALUES (%s) RETURNING id
                                """, (url,))
                conn.commit()
                return cursor.fetchone()[0], 'added_successfully'
            else:
                cursor.execute("SELECT (id) FROM urls WHERE name = (%s)", (url,))
                return cursor.fetchone()[0], 'already_exists'


def read_from_database(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM urls WHERE id = (%s)", (id,))
            values = cursor.fetchone()
            column_names = [desc[0] for desc in cursor.description]
            return dict(zip(column_names, values))


def read_full_from_database():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM urls")
            values = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            result = [dict(zip(column_names, value)) for value in values[::-1]]
            return result


# print(add_to_database('ya11112.ru'))
# print(add_to_database('ya23.ru'))
# print(add_to_database('ya11.ru'))
@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)



@app.route('/urls', methods=['GET', 'POST'])
def get_urls():
    url = request.form.get('url')
    if not url:
        data = read_full_from_database()
        return render_template('urls.html', data=data)
    if not validate_url(url) or len(url) > 255:
        flash('Некорректный URL', 'alert-danger')
        return redirect(url_for('index'))

    url_norm = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    id, status = add_to_database(url_norm)
    if status == 'added_successfully':
        flash('Страница успешно добавлена', 'alert-success')
    else:
        flash('Страница уже существует', 'alert-info')
    return redirect(url_for('get_url', id=id))


        # flash('Некорректный URL', 'alert-succes')
        # flash('Некорректный URL', 'alert-warning')
        # flash('Некорректный URL', 'alert-info')



@app.route('/urls/<int:id>')
def get_url(id):
    url = read_from_database(id)
    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html', url=url, messages=messages)


create_table()





# def get_urls():
#     url = request.form.get('url')
#     if not url:
#         data = read_full_from_database()
#         return render_template('urls.html', data=data)
#     if validate_url(url) and len(url) <= 255:
#         url_norm = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
#         id, status = add_to_database(url_norm)
#         if status == 'added_successfully':
#             flash('Страница успешно добавлена', 'alert-success')
#         else:
#             flash('Страница уже существует', 'alert-info')
#         return redirect(url_for('get_url', id=id))
#     else:
#         flash('Некорректный URL', 'alert-danger')
#         # flash('Некорректный URL', 'alert-succes')
#         # flash('Некорректный URL', 'alert-warning')
#         # flash('Некорректный URL', 'alert-info')
#         return redirect(url_for('index'))