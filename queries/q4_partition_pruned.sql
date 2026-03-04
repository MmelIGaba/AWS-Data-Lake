SELECT location, SUM(new_cases) AS new_cases
FROM datalake_db.processed
WHERE year = '2021' AND month = '1'
GROUP BY location
ORDER BY new_cases DESC
LIMIT 20;
