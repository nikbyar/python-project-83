import psycopg2
import os
import requests
from flask import Flask, render_template, request, redirect, \
    url_for, flash, get_flashed_messages
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url as validate_url
from bs4 import BeautifulSoup


app = Flask(__name__)

load_dotenv()


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


def create_table():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            with open('database.sql', 'r') as f:
                cursor.execute(f.read())
                conn.commit()


def add_to_urls(url):
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
                cursor.execute("SELECT (id) FROM urls WHERE name = (%s)",
                               (url,))
                return cursor.fetchone()[0], 'already_exists'


def read_from_database(table_name, id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = f"SELECT * FROM {table_name} WHERE id = %s"
            cursor.execute(query, (id,))
            values = cursor.fetchone()
            column_names = [desc[0] for desc in cursor.description]
            if not values:
                values = [[] for i in range(len(column_names))]
            return dict(zip(column_names, values))


def read_full_from_database(table_name, id='all'):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            if id == 'all':
                query = f"SELECT * FROM {table_name}"
                cursor.execute(query)
            else:
                query = f"SELECT * FROM {table_name} WHERE url_id = %s"
                cursor.execute(query, (id,))
            values = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            result = [dict(zip(column_names, value)) for value in values[::-1]]
            return result


def add_to_url_checks(url_id, status_code, h1, title, description):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                                INSERT INTO url_checks
                                (url_id, status_code, h1, title, description)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (url_id, status_code, h1, title, description))
            conn.commit()


def merge_tables():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                                SELECT DISTINCT ON (urls.id)
                                    urls.id, urls.name,
                                    checks.status_code, checks.created_at
                                FROM urls
                                LEFT JOIN url_checks AS checks
                                ON urls.id = checks.url_id
            """)
            conn.commit()
            values = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            result = [dict(zip(column_names, value)) for value in values]
            return result


def check_tags(response):
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.h1.string if soup.h1 else None
    title = soup.title.string if soup.title else None

    description = None
    if soup.find('meta', attrs={'name': 'description'}):
        description = soup.find('meta', attrs={'name': 'description'}).\
            get('content')

    return h1, title, description


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)


@app.route('/urls', methods=['GET', 'POST'])
def get_urls():
    url = request.form.get('url')
    if not url:
        data = merge_tables()
        return render_template('urls.html', data=data)
    if not validate_url(url) or len(url) > 255:
        flash('Некорректный URL', 'alert-danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', messages=messages), 422

    url_norm = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    id, status = add_to_urls(url_norm)
    if status == 'added_successfully':
        flash('Страница успешно добавлена', 'alert-success')
    else:
        flash('Страница уже существует', 'alert-info')
    return redirect(url_for('get_url', id=id))


@app.route('/urls/<int:id>')
def get_url(id):
    url = read_from_database('urls', id)
    messages = get_flashed_messages(with_categories=True)
    checks = read_full_from_database('url_checks', id)
    return render_template('url.html', url=url, checks=checks,
                           messages=messages)


@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    url = request.form.get('url')
    try:
        response = requests.get(url)
        if response.status_code == 200:
            h1, title, description = check_tags(response)
            add_to_url_checks(url_id, response.status_code, h1,
                              title, description)
            flash('Страница успешно проверена', 'alert-success')
        else:
            flash('Произошла ошибка при проверке', 'alert-danger')

    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'alert-danger')

    return redirect(url_for('get_checked_url', url_id=url_id))


@app.route('/urls/<int:url_id>/checks')
def get_checked_url(url_id):
    checks = read_full_from_database('url_checks', url_id)
    url = read_from_database('urls', url_id)
    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html', url=url, checks=checks,
                           messages=messages)


# create_table()
