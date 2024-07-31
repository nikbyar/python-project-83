check: lint test

install:
	poetry install


dev:
	poetry run flask --app page_analyzer:app run


lint:
	poetry run flake8 page_analyzer


test:
	poetry run pytest --cov=gendiff tests/ --cov-report xml

test-coverage:
	poetry run pytest --cov=gendiff --cov-report xml




