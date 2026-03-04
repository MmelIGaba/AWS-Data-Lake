SELECT location, MAX(total_deaths) AS total_deaths, MAX(total_cases) AS total_cases,
ROUND(MAX(total_deaths) / NULLIF(MAX(total_cases), 0) * 100, 2) AS death_rate_pct
FROM datalake_db.processed
GROUP BY location
ORDER BY death_rate_pct DESC
LIMIT 20;
