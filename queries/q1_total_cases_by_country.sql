SELECT location, MAX(total_cases) AS total_cases
FROM datalake_db.processed
GROUP BY location
ORDER BY total_cases DESC
LIMIT 20;
