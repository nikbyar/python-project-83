import os
import psycopg2
from psycopg2.extras import DictCursor
from bs4 import BeautifulSoup
from dotenv import load_dotenv
# from .app import app

load_dotenv()

# # current_app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
# DATABASE_URL = current_app.config['DATABASE_URL']
DATABASE_URL = os.getenv('DATABASE_URL')


def add_to_urls(url):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT (name) FROM urls")

            sites = [site[0] for site in cursor.fetchall()]
            if url not in sites:
                cursor.execute("""
                                INSERT INTO urls (name) VALUES (%s) RETURNING id
                                """, (url,))
                return cursor.fetchone()[0], 'added_successfully'
            else:
                cursor.execute("SELECT (id) FROM urls WHERE name = (%s)",
                               (url,))
                return cursor.fetchone()[0], 'already_exists'


def read_from_urls(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM urls WHERE id = %s"
            cursor.execute(query, (id,))
            values = cursor.fetchone()
            column_names = [desc[0] for desc in cursor.description]
            if not values:
                values = [[] for i in range(len(column_names))]
            return dict(zip(column_names, values))


def read_full_from_url_checks(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM url_checks WHERE url_id = %s"
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
