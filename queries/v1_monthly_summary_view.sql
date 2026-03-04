CREATE OR REPLACE VIEW datalake_db.monthly_summary AS
SELECT year, month,
SUM(new_cases) AS total_new_cases,
SUM(new_deaths) AS total_new_deaths,
SUM(new_vaccinations) AS total_new_vaccinations
FROM datalake_db.processed
GROUP BY year, month;
