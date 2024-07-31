#check: lint test

install:
	poetry install


dev:
	poetry run flask --app page_analyzer:app run


lint:
	poetry run flake8 page_analyzer


#test:
#	poetry run pytest --cov=app tests/ --cov-report xml
#
#test-coverage:
#	poetry run pytest --cov=app --cov-report xml

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app



