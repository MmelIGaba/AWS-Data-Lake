SELECT year, month, SUM(new_cases) AS monthly_new_cases
FROM datalake_db.processed
GROUP BY year, month
ORDER BY year, month;
