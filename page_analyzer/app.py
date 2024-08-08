import os
import requests
from flask import Flask, render_template, request, redirect, \
    url_for, flash, get_flashed_messages
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url as validate_url
from .db import add_to_urls, add_to_url_checks, check_tags, \
    read_from_urls, read_full_from_url_checks, \
    merge_tables


app = Flask(__name__)

load_dotenv()


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


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
    url = read_from_urls(id)
    messages = get_flashed_messages(with_categories=True)
    checks = read_full_from_url_checks(id)
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
    checks = read_full_from_url_checks(url_id)
    url = read_from_urls(url_id)
    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html', url=url, checks=checks,
                           messages=messages)
