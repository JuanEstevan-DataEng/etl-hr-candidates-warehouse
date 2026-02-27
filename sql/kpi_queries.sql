-- =====================================================================
-- Task 3: KPIs & Visualizations Queries
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Hires by Technology
-- Shows the total number of hired candidates grouped by their technical role.
-- ---------------------------------------------------------------------
SELECT 
    t.technology_name, 
    SUM(f.is_hired) AS total_hires
FROM fact_application f
JOIN dim_technology t ON f.technology_sk = t.technology_sk
WHERE f.is_hired = 1
GROUP BY t.technology_name
ORDER BY total_hires DESC;

-- ---------------------------------------------------------------------
-- 2. Hires by Year
-- Shows the hiring trend over the years.
-- ---------------------------------------------------------------------
SELECT 
    d.year, 
    SUM(f.is_hired) AS total_hires
FROM fact_application f
JOIN dim_date d ON f.date_sk = d.date_sk
WHERE f.is_hired = 1
GROUP BY d.year
ORDER BY d.year;

-- ---------------------------------------------------------------------
-- 3. Hires by Seniority
-- Displays the distribution of hired candidates based on their seniority level.
-- ---------------------------------------------------------------------
SELECT 
    s.seniority_name, 
    SUM(f.is_hired) AS total_hires
FROM fact_application f
JOIN dim_seniority s ON f.seniority_sk = s.seniority_sk
WHERE f.is_hired = 1
GROUP BY s.seniority_name
ORDER BY total_hires DESC;

-- ---------------------------------------------------------------------
-- 4. Hires by Country over Years (Focus on USA, Brazil, Colombia, Ecuador)
-- Compares the hiring trends across specific target countries.
-- Note: 'united states' is used based on the EDA lowercase transformation.
-- ---------------------------------------------------------------------
SELECT 
    l.country, 
    d.year, 
    SUM(f.is_hired) AS total_hires
FROM fact_application f
JOIN dim_location l ON f.location_sk = l.location_sk
JOIN dim_date d ON f.date_sk = d.date_sk
WHERE f.is_hired = 1 
  AND l.country IN ('united states', 'united states of america', 'usa', 'brazil', 'colombia', 'ecuador')
GROUP BY l.country, d.year
ORDER BY l.country, d.year;

-- ---------------------------------------------------------------------
-- 5. Additional KPI 1: Hire Rate (%) by Seniority
-- Analyzes the conversion rate of applications to hires per seniority level.
-- ---------------------------------------------------------------------
SELECT 
    s.seniority_name,
    COUNT(f.application_sk) AS total_applications,
    SUM(f.is_hired) AS total_hires,
    ROUND((SUM(f.is_hired) / COUNT(f.application_sk)) * 100, 2) AS hire_rate_percentage
FROM fact_application f
JOIN dim_seniority s ON f.seniority_sk = s.seniority_sk
GROUP BY s.seniority_name
ORDER BY hire_rate_percentage DESC;

-- ---------------------------------------------------------------------
-- 6. Additional KPI 2: Average Scores by Technology
-- Shows the average technical capabilities of candidates applying for each technology.
-- ---------------------------------------------------------------------
SELECT 
    t.technology_name,
    ROUND(AVG(f.code_challenge_score), 2) AS avg_code_score,
    ROUND(AVG(f.technical_interview_score), 2) AS avg_interview_score
FROM fact_application f
JOIN dim_technology t ON f.technology_sk = t.technology_sk
GROUP BY t.technology_name
ORDER BY avg_code_score DESC, avg_interview_score DESC;
