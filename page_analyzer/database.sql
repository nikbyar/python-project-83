DROP TABLE IF EXISTS urls, url_checks;
CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at DATE DEFAULT CURRENT_DATE
);
CREATE TABLE IF NOT EXISTS url_checks (
    id SERIAL PRIMARY KEY,
    url_id INT REFERENCES urls(id) NOT NULL,
    status_code INT,
    h1 VARCHAR(255),
    title VARCHAR(255),
    description VARCHAR(255),
    created_at DATE
    );