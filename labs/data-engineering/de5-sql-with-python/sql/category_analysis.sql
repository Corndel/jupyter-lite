SELECT 
    c.name AS category_name,
    COUNT(f.film_id) AS film_count,
    AVG(f.rental_rate) AS avg_rental_rate,
    AVG(f.length) AS avg_length
FROM
    category c
INNER JOIN 
    film_category fc ON c.category_id = fc.category_id
INNER JOIN
    film f ON fc.film_id = f.film_id
WHERE
    f.rental_rate > 0.99
GROUP BY
    c.name
ORDER BY 
    film_count DESC;