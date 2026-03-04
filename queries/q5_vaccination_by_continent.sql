SELECT continent, MAX(people_fully_vaccinated_per_hundred) AS fully_vaccinated_pct
FROM datalake_db.processed
WHERE continent IS NOT NULL
GROUP BY continent
ORDER BY fully_vaccinated_pct DESC;
