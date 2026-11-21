"""
Build sakila.sqlite for the DE5 Advanced SQL lab.

The Azure SQL learning environment this lab replaces loaded Sakila from
Corndel/sakila (a fork of jOOQ/sakila, BSD 2-Clause licence; see
SAKILA-LICENSE.txt). This script loads the same rows into SQLite:

- The schema below is a port of sql-server-sakila-db/sql-server-sakila-schema.sql,
  so the tables behave as they did in Azure SQL: IDENTITY columns become
  INTEGER PRIMARY KEY AUTOINCREMENT, and DEFAULT (getdate()) becomes
  DEFAULT CURRENT_TIMESTAMP. It has no triggers, so last_update keeps the
  values in the data.
- The rows come from sqlite-sakila-db/sqlite-sakila-insert-data.sql at a
  pinned commit, which holds the same data as the SQL Server insert script.

Run it from anywhere:  python generate_db.py
"""

import os
import sqlite3
import urllib.request

COMMIT = "2aceb1b515d3d202d48e0d7ed75499f27d49dd63"
DATA_URL = (
    f"https://raw.githubusercontent.com/Corndel/sakila/{COMMIT}"
    "/sqlite-sakila-db/sqlite-sakila-insert-data.sql"
)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sakila.sqlite")

SCHEMA = """
CREATE TABLE actor (
  actor_id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name VARCHAR(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_actor_last_name ON actor(last_name);

CREATE TABLE country (
  country_id INTEGER PRIMARY KEY AUTOINCREMENT,
  country VARCHAR(50) NOT NULL,
  last_update DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE city (
  city_id INTEGER PRIMARY KEY AUTOINCREMENT,
  city VARCHAR(50) NOT NULL,
  country_id INT NOT NULL REFERENCES country (country_id),
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_country_id ON city(country_id);

CREATE TABLE address (
  address_id INTEGER PRIMARY KEY AUTOINCREMENT,
  address VARCHAR(50) NOT NULL,
  address2 VARCHAR(50) DEFAULT NULL,
  district VARCHAR(20) NOT NULL,
  city_id INT NOT NULL REFERENCES city (city_id),
  postal_code VARCHAR(10) DEFAULT NULL,
  phone VARCHAR(20) NOT NULL,
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_city_id ON address(city_id);

CREATE TABLE language (
  language_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name CHAR(20) NOT NULL,
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE category (
  category_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(25) NOT NULL,
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer (
  customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  store_id INT NOT NULL REFERENCES store (store_id),
  first_name VARCHAR(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  email VARCHAR(50) DEFAULT NULL,
  address_id INT NOT NULL REFERENCES address (address_id),
  active CHAR(1) NOT NULL DEFAULT 'Y',
  create_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_store_id ON customer(store_id);
CREATE INDEX idx_fk_address_id ON customer(address_id);
CREATE INDEX idx_last_name ON customer(last_name);

CREATE TABLE film (
  film_id INTEGER PRIMARY KEY AUTOINCREMENT,
  title VARCHAR(255) NOT NULL,
  description TEXT DEFAULT NULL,
  release_year VARCHAR(4) NULL,
  language_id INT NOT NULL REFERENCES language (language_id),
  original_language_id INT DEFAULT NULL REFERENCES language (language_id),
  rental_duration TINYINT NOT NULL DEFAULT 3,
  rental_rate DECIMAL(4,2) NOT NULL DEFAULT 4.99,
  length SMALLINT DEFAULT NULL,
  replacement_cost DECIMAL(5,2) NOT NULL DEFAULT 19.99,
  rating VARCHAR(10) DEFAULT 'G'
    CHECK (rating IN ('G','PG','PG-13','R','NC-17')),
  special_features VARCHAR(255) DEFAULT NULL
    CHECK (special_features IS NULL OR
           special_features LIKE '%Trailers%' OR
           special_features LIKE '%Commentaries%' OR
           special_features LIKE '%Deleted Scenes%' OR
           special_features LIKE '%Behind the Scenes%'),
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_language_id ON film(language_id);
CREATE INDEX idx_fk_original_language_id ON film(original_language_id);

CREATE TABLE film_actor (
  actor_id INT NOT NULL REFERENCES actor (actor_id),
  film_id INT NOT NULL REFERENCES film (film_id),
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (actor_id, film_id)
);
CREATE INDEX idx_fk_film_actor_film ON film_actor(film_id);
CREATE INDEX idx_fk_film_actor_actor ON film_actor(actor_id);

CREATE TABLE film_category (
  film_id INT NOT NULL REFERENCES film (film_id),
  category_id INT NOT NULL REFERENCES category (category_id),
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (film_id, category_id)
);
CREATE INDEX idx_fk_film_category_film ON film_category(film_id);
CREATE INDEX idx_fk_film_category_category ON film_category(category_id);

CREATE TABLE film_text (
  film_id INT NOT NULL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE inventory (
  inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
  film_id INT NOT NULL REFERENCES film (film_id),
  store_id INT NOT NULL REFERENCES store (store_id),
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_film_id ON inventory(film_id);
CREATE INDEX idx_fk_film_id_store_id ON inventory(store_id, film_id);

CREATE TABLE staff (
  staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name VARCHAR(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  address_id INT NOT NULL REFERENCES address (address_id),
  picture BLOB DEFAULT NULL,
  email VARCHAR(50) DEFAULT NULL,
  store_id INT NOT NULL REFERENCES store (store_id),
  active BIT NOT NULL DEFAULT 1,
  username VARCHAR(16) NOT NULL,
  password VARCHAR(40) DEFAULT NULL,
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_staff_store_id ON staff(store_id);
CREATE INDEX idx_fk_staff_address_id ON staff(address_id);

CREATE TABLE store (
  store_id INTEGER PRIMARY KEY AUTOINCREMENT,
  manager_staff_id INT NOT NULL REFERENCES staff (staff_id),
  address_id INT NOT NULL REFERENCES address (address_id),
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_unique_manager ON store(manager_staff_id);
CREATE INDEX idx_fk_store_address ON store(address_id);

CREATE TABLE payment (
  payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INT NOT NULL REFERENCES customer (customer_id),
  staff_id INT NOT NULL REFERENCES staff (staff_id),
  rental_id INT DEFAULT NULL REFERENCES rental (rental_id),
  amount DECIMAL(5,2) NOT NULL,
  payment_date DATETIME NOT NULL,
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_payment_staff_id ON payment(staff_id);
CREATE INDEX idx_fk_payment_customer_id ON payment(customer_id);

CREATE TABLE rental (
  rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
  rental_date DATETIME NOT NULL,
  inventory_id INT NOT NULL REFERENCES inventory (inventory_id),
  customer_id INT NOT NULL REFERENCES customer (customer_id),
  return_date DATETIME DEFAULT NULL,
  staff_id INT NOT NULL REFERENCES staff (staff_id),
  last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_inventory_id ON rental(inventory_id);
CREATE INDEX idx_fk_customer_id ON rental(customer_id);
CREATE INDEX idx_fk_rental_staff_id ON rental(staff_id);
CREATE UNIQUE INDEX idx_uq ON rental(rental_date, inventory_id, customer_id);

CREATE VIEW customer_list AS
SELECT cu.customer_id AS ID,
       cu.first_name || ' ' || cu.last_name AS name,
       a.address AS address,
       a.postal_code AS zip_code,
       a.phone AS phone,
       city.city AS city,
       country.country AS country,
       CASE WHEN cu.active = 1 THEN 'active' ELSE '' END AS notes,
       cu.store_id AS SID
FROM customer AS cu
JOIN address AS a ON cu.address_id = a.address_id
JOIN city ON a.city_id = city.city_id
JOIN country ON city.country_id = country.country_id;

CREATE VIEW film_list AS
SELECT film.film_id AS FID,
       film.title AS title,
       film.description AS description,
       category.name AS category,
       film.rental_rate AS price,
       film.length AS length,
       film.rating AS rating,
       actor.first_name || ' ' || actor.last_name AS actors
FROM category
LEFT JOIN film_category ON category.category_id = film_category.category_id
LEFT JOIN film ON film_category.film_id = film.film_id
JOIN film_actor ON film.film_id = film_actor.film_id
JOIN actor ON film_actor.actor_id = actor.actor_id;

CREATE VIEW staff_list AS
SELECT s.staff_id AS ID,
       s.first_name || ' ' || s.last_name AS name,
       a.address AS address,
       a.postal_code AS zip_code,
       a.phone AS phone,
       city.city AS city,
       country.country AS country,
       s.store_id AS SID
FROM staff AS s
JOIN address AS a ON s.address_id = a.address_id
JOIN city ON a.city_id = city.city_id
JOIN country ON city.country_id = country.country_id;

CREATE VIEW sales_by_store AS
SELECT s.store_id,
       c.city || ',' || cy.country AS store,
       m.first_name || ' ' || m.last_name AS manager,
       SUM(p.amount) AS total_sales
FROM payment AS p
INNER JOIN rental AS r ON p.rental_id = r.rental_id
INNER JOIN inventory AS i ON r.inventory_id = i.inventory_id
INNER JOIN store AS s ON i.store_id = s.store_id
INNER JOIN address AS a ON s.address_id = a.address_id
INNER JOIN city AS c ON a.city_id = c.city_id
INNER JOIN country AS cy ON c.country_id = cy.country_id
INNER JOIN staff AS m ON s.manager_staff_id = m.staff_id
GROUP BY s.store_id, c.city || ',' || cy.country, m.first_name || ' ' || m.last_name;

CREATE VIEW sales_by_film_category AS
SELECT c.name AS category,
       SUM(p.amount) AS total_sales
FROM payment AS p
INNER JOIN rental AS r ON p.rental_id = r.rental_id
INNER JOIN inventory AS i ON r.inventory_id = i.inventory_id
INNER JOIN film AS f ON i.film_id = f.film_id
INNER JOIN film_category AS fc ON f.film_id = fc.film_id
INNER JOIN category AS c ON fc.category_id = c.category_id
GROUP BY c.name;
"""


def main():
    print(f"Downloading {DATA_URL}")
    with urllib.request.urlopen(DATA_URL) as response:
        data_sql = response.read().decode("utf-8")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    # One transaction, or SQLite commits (and syncs) after every insert
    conn.executescript("BEGIN;\n" + data_sql + "\nCOMMIT;")

    for table in ["actor", "category", "customer", "film", "inventory",
                  "payment", "rental", "staff", "store"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n} rows")

    conn.execute("VACUUM")
    conn.close()
    print(f"Wrote {DB_PATH}")


if __name__ == "__main__":
    main()
