"""
Build pagila.sqlite for the DE5 SQL learning environment lab.

The AWS learning environment this lab replaces loaded Pagila into PostgreSQL
from devrimgunduz/pagila (PostgreSQL licence; see PAGILA-LICENSE.txt). This
script loads the same rows into SQLite:

- The schema below is a port of pagila-schema.sql. Sequences become
  INTEGER PRIMARY KEY AUTOINCREMENT, DEFAULT now() becomes DEFAULT
  CURRENT_TIMESTAMP, the mpaa_rating type and year domain become CHECK
  constraints, booleans become 0/1, and the payment partitions
  (payment_p2022_01 to _07) become one payment table.
- The rows come from pagila-data.sql at a pinned commit: the same files as
  sql_scripts/ in Corndel/DE-sql-learning-environment-AWS.

What does not port: PL/pgSQL functions (film_in_stock, get_customer_balance,
rewards_report and others), triggers (last_updated, film_fulltext_trigger),
the tsvector full-text index, the group_concat aggregate (SQLite has a
built-in group_concat), the materialized view (a plain view here) and table
partitioning. film.special_features keeps PostgreSQL's array text, such as
{Trailers,"Deleted Scenes"}, and film.fulltext keeps the tsvector text.

Run it from anywhere:  python generate_db.py
"""

import os
import sqlite3
import urllib.request

COMMIT = "5ba5a57aeb159f75f02aca2432d3c262186d13d3"
DATA_URL = f"https://raw.githubusercontent.com/devrimgunduz/pagila/{COMMIT}/pagila-data.sql"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pagila.sqlite")

FK = "ON UPDATE CASCADE ON DELETE RESTRICT"

SCHEMA = f"""
CREATE TABLE actor (
  actor_id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_actor_last_name ON actor(last_name);

CREATE TABLE country (
  country_id INTEGER PRIMARY KEY AUTOINCREMENT,
  country TEXT NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE city (
  city_id INTEGER PRIMARY KEY AUTOINCREMENT,
  city TEXT NOT NULL,
  country_id INTEGER NOT NULL REFERENCES country(country_id) {FK},
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_country_id ON city(country_id);

CREATE TABLE address (
  address_id INTEGER PRIMARY KEY AUTOINCREMENT,
  address TEXT NOT NULL,
  address2 TEXT,
  district TEXT NOT NULL,
  city_id INTEGER NOT NULL REFERENCES city(city_id) {FK},
  postal_code TEXT,
  phone TEXT NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_city_id ON address(city_id);

CREATE TABLE category (
  category_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE language (
  language_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name CHARACTER(20) NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE film (
  film_id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  release_year INTEGER CHECK (release_year BETWEEN 1901 AND 2155),
  language_id INTEGER NOT NULL REFERENCES language(language_id) {FK},
  original_language_id INTEGER REFERENCES language(language_id) {FK},
  rental_duration SMALLINT NOT NULL DEFAULT 3,
  rental_rate NUMERIC(4,2) NOT NULL DEFAULT 4.99,
  length SMALLINT,
  replacement_cost NUMERIC(5,2) NOT NULL DEFAULT 19.99,
  rating TEXT DEFAULT 'G' CHECK (rating IN ('G', 'PG', 'PG-13', 'R', 'NC-17')),
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  special_features TEXT,
  fulltext TEXT NOT NULL
);
CREATE INDEX idx_fk_language_id ON film(language_id);
CREATE INDEX idx_fk_original_language_id ON film(original_language_id);
CREATE INDEX idx_title ON film(title);

CREATE TABLE film_actor (
  actor_id INTEGER NOT NULL REFERENCES actor(actor_id) {FK},
  film_id INTEGER NOT NULL REFERENCES film(film_id) {FK},
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (actor_id, film_id)
);
CREATE INDEX idx_fk_film_id ON film_actor(film_id);

CREATE TABLE film_category (
  film_id INTEGER NOT NULL REFERENCES film(film_id) {FK},
  category_id INTEGER NOT NULL REFERENCES category(category_id) {FK},
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (film_id, category_id)
);

CREATE TABLE store (
  store_id INTEGER PRIMARY KEY AUTOINCREMENT,
  manager_staff_id INTEGER NOT NULL,
  address_id INTEGER NOT NULL REFERENCES address(address_id) {FK},
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_unq_manager_staff_id ON store(manager_staff_id);

CREATE TABLE staff (
  staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  address_id INTEGER NOT NULL REFERENCES address(address_id) {FK},
  email TEXT,
  store_id INTEGER NOT NULL REFERENCES store(store_id),
  active BOOLEAN NOT NULL DEFAULT 1,
  username TEXT NOT NULL,
  password TEXT,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  picture BLOB
);

CREATE TABLE customer (
  customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  store_id INTEGER NOT NULL REFERENCES store(store_id) {FK},
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT,
  address_id INTEGER NOT NULL REFERENCES address(address_id) {FK},
  activebool BOOLEAN NOT NULL DEFAULT 1,
  create_date DATE NOT NULL DEFAULT CURRENT_DATE,
  last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  active INTEGER
);
CREATE INDEX idx_fk_address_id ON customer(address_id);
CREATE INDEX idx_fk_store_id ON customer(store_id);
CREATE INDEX idx_last_name ON customer(last_name);

CREATE TABLE inventory (
  inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
  film_id INTEGER NOT NULL REFERENCES film(film_id) {FK},
  store_id INTEGER NOT NULL REFERENCES store(store_id) {FK},
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_store_id_film_id ON inventory(store_id, film_id);

CREATE TABLE rental (
  rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
  rental_date TIMESTAMP NOT NULL,
  inventory_id INTEGER NOT NULL REFERENCES inventory(inventory_id) {FK},
  customer_id INTEGER NOT NULL REFERENCES customer(customer_id) {FK},
  return_date TIMESTAMP,
  staff_id INTEGER NOT NULL REFERENCES staff(staff_id) {FK},
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_inventory_id ON rental(inventory_id);
CREATE UNIQUE INDEX idx_unq_rental_rental_date_inventory_id_customer_id ON rental(rental_date, inventory_id, customer_id);

-- In PostgreSQL, payment is partitioned by month (payment_p2022_01 to _07);
-- here it is one table
CREATE TABLE payment (
  payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL REFERENCES customer(customer_id),
  staff_id INTEGER NOT NULL REFERENCES staff(staff_id),
  rental_id INTEGER NOT NULL REFERENCES rental(rental_id),
  amount NUMERIC(5,2) NOT NULL,
  payment_date TIMESTAMP NOT NULL
);
CREATE INDEX idx_fk_payment_customer_id ON payment(customer_id);
CREATE INDEX idx_fk_payment_staff_id ON payment(staff_id);

CREATE VIEW actor_info AS
SELECT a.actor_id, a.first_name, a.last_name,
       (SELECT group_concat(info, ', ')
        FROM (SELECT DISTINCT c.name || ': ' || (
                  SELECT group_concat(f.title, ', ')
                  FROM film f
                  JOIN film_category fc_1 ON f.film_id = fc_1.film_id
                  JOIN film_actor fa_1 ON f.film_id = fa_1.film_id
                  WHERE fc_1.category_id = c.category_id AND fa_1.actor_id = a.actor_id
                  GROUP BY fa_1.actor_id) AS info
              FROM film_actor fa
              JOIN film_category fc ON fa.film_id = fc.film_id
              JOIN category c ON fc.category_id = c.category_id
              WHERE fa.actor_id = a.actor_id)) AS film_info
FROM actor a;

CREATE VIEW customer_list AS
SELECT cu.customer_id AS id,
       cu.first_name || ' ' || cu.last_name AS name,
       a.address, a.postal_code AS "zip code", a.phone, city.city, country.country,
       CASE WHEN cu.activebool THEN 'active' ELSE '' END AS notes,
       cu.store_id AS sid
FROM customer cu
JOIN address a ON cu.address_id = a.address_id
JOIN city ON a.city_id = city.city_id
JOIN country ON city.country_id = country.country_id;

CREATE VIEW film_list AS
SELECT film.film_id AS fid, film.title, film.description, category.name AS category,
       film.rental_rate AS price, film.length, film.rating,
       group_concat(actor.first_name || ' ' || actor.last_name, ', ') AS actors
FROM category
LEFT JOIN film_category ON category.category_id = film_category.category_id
LEFT JOIN film ON film_category.film_id = film.film_id
JOIN film_actor ON film.film_id = film_actor.film_id
JOIN actor ON film_actor.actor_id = actor.actor_id
GROUP BY film.film_id, film.title, film.description, category.name, film.rental_rate, film.length, film.rating;

CREATE VIEW nicer_but_slower_film_list AS
SELECT film.film_id AS fid, film.title, film.description, category.name AS category,
       film.rental_rate AS price, film.length, film.rating,
       group_concat(upper(substr(actor.first_name, 1, 1)) || lower(substr(actor.first_name, 2))
                    || upper(substr(actor.last_name, 1, 1)) || lower(substr(actor.last_name, 2)), ', ') AS actors
FROM category
LEFT JOIN film_category ON category.category_id = film_category.category_id
LEFT JOIN film ON film_category.film_id = film.film_id
JOIN film_actor ON film.film_id = film_actor.film_id
JOIN actor ON film_actor.actor_id = actor.actor_id
GROUP BY film.film_id, film.title, film.description, category.name, film.rental_rate, film.length, film.rating;

-- A materialized view in PostgreSQL; SQLite has none, so this is a plain view
CREATE VIEW rental_by_category AS
SELECT c.name AS category, sum(p.amount) AS total_sales
FROM payment p
JOIN rental r ON p.rental_id = r.rental_id
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN film f ON i.film_id = f.film_id
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id
GROUP BY c.name
ORDER BY sum(p.amount) DESC;

CREATE VIEW sales_by_film_category AS
SELECT c.name AS category, sum(p.amount) AS total_sales
FROM payment p
JOIN rental r ON p.rental_id = r.rental_id
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN film f ON i.film_id = f.film_id
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id
GROUP BY c.name
ORDER BY sum(p.amount) DESC;

CREATE VIEW sales_by_store AS
SELECT c.city || ',' || cy.country AS store,
       m.first_name || ' ' || m.last_name AS manager,
       sum(p.amount) AS total_sales
FROM payment p
JOIN rental r ON p.rental_id = r.rental_id
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN store s ON i.store_id = s.store_id
JOIN address a ON s.address_id = a.address_id
JOIN city c ON a.city_id = c.city_id
JOIN country cy ON c.country_id = cy.country_id
JOIN staff m ON s.manager_staff_id = m.staff_id
GROUP BY cy.country, c.city, s.store_id, m.first_name, m.last_name
ORDER BY cy.country, c.city;

CREATE VIEW staff_list AS
SELECT s.staff_id AS id,
       s.first_name || ' ' || s.last_name AS name,
       a.address, a.postal_code AS "zip code", a.phone, city.city, country.country,
       s.store_id AS sid
FROM staff s
JOIN address a ON s.address_id = a.address_id
JOIN city ON a.city_id = city.city_id
JOIN country ON city.country_id = country.country_id;
"""

BOOLEAN_COLUMNS = {("customer", "activebool"), ("staff", "active")}
ESCAPES = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\"}


def unescape(field):
    """Decode one field of PostgreSQL's COPY text format."""
    if field == "\\N":
        return None
    out, i = [], 0
    while i < len(field):
        ch = field[i]
        if ch == "\\" and i + 1 < len(field):
            nxt = field[i + 1]
            out.append(ESCAPES.get(nxt, nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def convert(table, column, value):
    if value is None:
        return None
    if (table, column) in BOOLEAN_COLUMNS:
        return 1 if value == "t" else 0
    if table == "staff" and column == "picture" and value.startswith("\\x"):
        return bytes.fromhex(value[2:])
    return value


def copy_blocks(sql):
    """Yield (table, columns, rows) for each COPY ... FROM stdin block."""
    lines = iter(sql.splitlines())
    for line in lines:
        if not line.startswith("COPY public."):
            continue
        head = line[len("COPY public."):]
        table = head.split(" ", 1)[0]
        columns = [c.strip() for c in head[head.index("(") + 1:head.index(")")].split(",")]
        rows = []
        for row in lines:
            if row == "\\.":
                break
            fields = [unescape(f) for f in row.split("\t")]
            rows.append(fields)
        if table.startswith("payment_p"):
            table = "payment"
        yield table, columns, rows


def main():
    print(f"Downloading {DATA_URL}")
    with urllib.request.urlopen(DATA_URL) as response:
        data_sql = response.read().decode("utf-8")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    with conn:
        for table, columns, rows in copy_blocks(data_sql):
            placeholders = ", ".join("?" for _ in columns)
            conn.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                ([convert(table, c, v) for c, v in zip(columns, row)] for row in rows),
            )
    for table in ["actor", "address", "category", "city", "country", "customer", "film",
                  "film_actor", "film_category", "inventory", "language", "payment",
                  "rental", "staff", "store"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n} rows")
    problems = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  foreign key problems: {len(problems)}")
    conn.execute("VACUUM")
    conn.close()
    print(f"Wrote {DB_PATH}")


if __name__ == "__main__":
    main()
