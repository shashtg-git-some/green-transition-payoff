-- ============================================================================
-- EU GREEN TRANSITION: SQL ANALYTICS PORTFOLIO
-- Dataset: eu_energy_panel (2010 - 2023)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Average Renewable Share per Country (All Years)
-- Concept Demonstrated: Basic Aggregation (AVG) and Ordering
-- Analytical Insight: Identifies the historical leaders in renewable energy 
-- adoption across the entire 14-year panel.
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    ROUND(AVG(elec_gen_renewables_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) * 100, 2) AS avg_renewable_share_pct
FROM eu_energy_panel
GROUP BY country_name
ORDER BY avg_renewable_share_pct DESC;

-- ----------------------------------------------------------------------------
-- QUERY 2: Total Fossil Fuel Import Cost per Country in the Crisis Year (2022)
-- Concept Demonstrated: Conditional Filtering (WHERE) and Calculated Columns
-- Analytical Insight: Quantifies financial vulnerability. By multiplying fossil 
-- generation by the crisis-year electricity price, we estimate the theoretical 
-- market cost burden for grids relying on fossil fuels during the 2022 gas shock.
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    ROUND((elec_gen_fossil_twh * 1000) * elec_price_eur_kwh, 2) AS estimated_fossil_cost_millions_eur
FROM eu_energy_panel
WHERE year = 2022
ORDER BY estimated_fossil_cost_millions_eur DESC;

-- ----------------------------------------------------------------------------
-- QUERY 3: EU-Wide Average Carbon Price Timeline (2010 - 2023)
-- Concept Demonstrated: Time-Series Aggregation
-- Analytical Insight: Tracks the macro-level regulatory pressure. Shows the 
-- prolonged period of stagnation followed by the aggressive post-2018 price rally.
-- ----------------------------------------------------------------------------
SELECT 
    year,
    ROUND(AVG(carbon_price_eur_tonne), 2) AS avg_eu_carbon_price
FROM eu_energy_panel
GROUP BY year
ORDER BY year ASC;

-- ----------------------------------------------------------------------------
-- QUERY 4: Count of Countries Exceeding 40% Renewable Share by Year
-- Concept Demonstrated: Subqueries / Common Table Expressions (CTE) with COUNT
-- Analytical Insight: Measures the pace of the continent's transition. If the count
-- increases over time, it proves the structural shift away from fossil fuels.
-- ----------------------------------------------------------------------------
WITH YearlyShares AS (
    SELECT 
        year,
        country_name,
        (elec_gen_renewables_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) AS renewable_share
    FROM eu_energy_panel
)
SELECT 
    year,
    COUNT(country_name) AS countries_above_40_pct
FROM YearlyShares
WHERE renewable_share >= 0.40
GROUP BY year
ORDER BY year ASC;

-- ----------------------------------------------------------------------------
-- QUERY 5: Top 5 Countries by Renewable Capacity Growth (2010 vs 2022)
-- Concept Demonstrated: Conditional Aggregation and On-the-Fly Data Engineering
-- Analytical Insight: Shifts focus from "historical leaders" to "fastest movers." 
-- Because raw capacity data was incomplete, this query dynamically derives capacity 
-- from actual generation (TWh) using the standard European 25% capacity factor (456.62).
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    ROUND(SUM(CASE WHEN year = 2022 THEN (elec_gen_renewables_twh * 456.62) ELSE 0 END) - 
          SUM(CASE WHEN year = 2010 THEN (elec_gen_renewables_twh * 456.62) ELSE 0 END), 2) AS capacity_growth_mw
FROM eu_energy_panel
WHERE year IN (2010, 2022)
GROUP BY country_name
ORDER BY capacity_growth_mw DESC
LIMIT 5;

-- ----------------------------------------------------------------------------
-- QUERY 6: Top 5 Countries Reducing Import Dependency (2010 vs 2022)
-- Concept Demonstrated: Conditional Aggregation and Difference Calculation
-- Analytical Insight: Proves which countries successfully used the energy 
-- transition to increase their sovereign energy security and reduce reliance 
-- on foreign power imports prior to the peak of the crisis.
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    ROUND(SUM(CASE WHEN year = 2010 THEN net_imports_gwh ELSE 0 END) - 
          SUM(CASE WHEN year = 2022 THEN net_imports_gwh ELSE 0 END), 2) AS import_reduction_gwh
FROM eu_energy_panel
WHERE year IN (2010, 2022)
GROUP BY country_name
ORDER BY import_reduction_gwh DESC
LIMIT 5;

-- ----------------------------------------------------------------------------
-- QUERY 7: The Carbon Price Threshold (Exceeding €25/tonne)
-- Concept Demonstrated: Distinct Filtering and Hardcoded Flagging
-- Analytical Insight: Isolates the specific macroeconomic moments where the 
-- EU ETS carbon price broke out of its stagnation phase. Using DISTINCT removes 
-- redundant country-level rows, as the EU ETS price is identical continent-wide.
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    year,
    carbon_price_eur_tonne,
    'Threshold Crossed' AS market_signal
FROM eu_energy_panel
WHERE carbon_price_eur_tonne > 25.00
ORDER BY year ASC;

-- ----------------------------------------------------------------------------
-- QUERY 8: Electricity Price Volatility Ranking (2021 - 2023)
-- Concept Demonstrated: Statistical Aggregation (STDDEV) and Range Filtering
-- Analytical Insight: Identifies which grid architectures were the most (and least) 
-- financially stable during the Russian gas supply shock.
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    ROUND(STDDEV(elec_price_eur_kwh), 4) AS price_volatility_index
FROM eu_energy_panel
WHERE year BETWEEN 2021 AND 2023
GROUP BY country_name
ORDER BY price_volatility_index DESC;

-- ----------------------------------------------------------------------------
-- QUERY 9: Year-on-Year Change in EU Average Carbon Price
-- Concept Demonstrated: Window Functions (LAG) over a CTE
-- Analytical Insight: Calculates the velocity of the carbon tax. By placing the 
-- previous year's price next to the current year, we can calculate the exact 
-- €/tonne shock the market experienced annually.
-- ----------------------------------------------------------------------------
WITH YearlyPrice AS (
    SELECT 
        year, 
        ROUND(AVG(carbon_price_eur_tonne), 2) AS avg_price
    FROM eu_energy_panel
    GROUP BY year
)
SELECT 
    year,
    avg_price AS current_year_price,
    LAG(avg_price) OVER (ORDER BY year ASC) AS previous_year_price,
    ROUND(avg_price - LAG(avg_price) OVER (ORDER BY year ASC), 2) AS yoy_change_eur
FROM YearlyPrice;

-- ----------------------------------------------------------------------------
-- QUERY 10: Year-on-Year Change in Renewable Capacity per Country
-- Concept Demonstrated: Advanced Window Functions (LAG with PARTITION BY)
-- Analytical Insight: Tracks physical infrastructure momentum. The PARTITION BY 
-- clause isolates each country's timeline to identify exactly which years saw 
-- the biggest aggressive spikes in wind/solar installations.
-- ----------------------------------------------------------------------------
WITH CountryCapacity AS (
    SELECT 
        country_name,
        year,
        ROUND(elec_gen_renewables_twh * 456.62, 2) AS capacity_mw
    FROM eu_energy_panel
)
SELECT 
    country_name,
    year,
    capacity_mw AS current_capacity,
    LAG(capacity_mw) OVER (PARTITION BY country_name ORDER BY year ASC) AS prev_capacity,
    ROUND(capacity_mw - LAG(capacity_mw) OVER (PARTITION BY country_name ORDER BY year ASC), 2) AS yoy_capacity_added
FROM CountryCapacity
ORDER BY yoy_capacity_added DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- QUERY 11: 2022 Renewable Share Rankings
-- Concept Demonstrated: Window Functions (RANK)
-- Analytical Insight: Evaluates the competitive landscape during the energy crisis.
-- Unlike simple ORDER BY, RANK() securely handles ties and provides a definitive 
-- leaderboard metric for grid cleanliness.
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    ROUND((elec_gen_renewables_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) * 100, 2) AS renewable_share_pct,
    RANK() OVER (ORDER BY (elec_gen_renewables_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) DESC) AS country_rank
FROM eu_energy_panel
WHERE year = 2022;

-- ----------------------------------------------------------------------------
-- QUERY 12: Pre-2019 vs Post-2019 Renewable Acceleration
-- Concept Demonstrated: Multiple Common Table Expressions (CTEs) and JOINs
-- Analytical Insight: Splits the timeline exactly when the carbon price spiked 
-- (€25+ threshold). Proves mathematically which countries accelerated their 
-- transition fastest after the regulatory environment became hostile to fossil fuels.
-- ----------------------------------------------------------------------------
WITH Pre2019 AS (
    SELECT 
        country_name, 
        AVG(elec_gen_renewables_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) AS pre_share
    FROM eu_energy_panel 
    WHERE year < 2019 
    GROUP BY country_name
),
Post2019 AS (
    SELECT 
        country_name, 
        AVG(elec_gen_renewables_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) AS post_share
    FROM eu_energy_panel 
    WHERE year >= 2019 
    GROUP BY country_name
)
SELECT 
    pr.country_name,
    ROUND(pr.pre_share * 100, 2) AS pre_2019_share_pct,
    ROUND(po.post_share * 100, 2) AS post_2019_share_pct,
    ROUND((po.post_share - pr.pre_share) * 100, 2) AS share_acceleration_pct
FROM Pre2019 pr
JOIN Post2019 po ON pr.country_name = po.country_name
ORDER BY share_acceleration_pct DESC;

-- ----------------------------------------------------------------------------
-- QUERY 13: 2022 Import Dependency vs EU Average
-- Concept Demonstrated: Scalar Subqueries inside a CASE statement
-- Analytical Insight: Benchmarks sovereign energy security. Dynamically calculates 
-- the EU-wide average import volume, then evaluates each specific country against 
-- that moving target during the gas shock.
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    net_imports_gwh,
    CASE 
        WHEN net_imports_gwh > (SELECT AVG(net_imports_gwh) FROM eu_energy_panel WHERE year = 2022) 
        THEN 'Above Average'
        ELSE 'Below Average'
    END AS import_dependency_status
FROM eu_energy_panel
WHERE year = 2022
ORDER BY net_imports_gwh DESC;

-- ----------------------------------------------------------------------------
-- QUERY 14: The 2022 Executive Scorecard
-- Concept Demonstrated: Comprehensive Multi-Metric Aggregation
-- Analytical Insight: Creates a single, unified view of a country's energy profile 
-- during the most severe year of the crisis. It combines grid cleanliness, energy 
-- independence, and consumer financial impact into one scannable dashboard.
-- ----------------------------------------------------------------------------
SELECT 
    country_name,
    ROUND((elec_gen_renewables_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) * 100, 2) AS renewable_share_pct,
    net_imports_gwh AS import_reliance,
    carbon_price_eur_tonne AS market_carbon_tax,
    ROUND(elec_price_eur_kwh, 3) AS consumer_electricity_price
FROM eu_energy_panel
WHERE year = 2022
ORDER BY renewable_share_pct DESC;

-- ----------------------------------------------------------------------------
-- QUERY 15: The Grand Conclusion (Cohort Transition 2010 vs 2022)
-- Concept Demonstrated: Advanced CTEs, Cohort Assignment, and Delta Calculations
-- Analytical Insight: This mirrors the panel regression model. It splits Europe 
-- into "Dirty" vs "Clean" grids based on their 2010 starting point. It then proves 
-- that when the carbon price spiked, the "Dirty" cohort was forced to eliminate 
-- a massive amount of their fossil generation, while the "Clean" cohort eliminated
-- relatively less.
-- ----------------------------------------------------------------------------
WITH Baseline2010 AS (
    -- Step 1: Establish who was dirty and who was clean in 2010
    SELECT 
        country_name,
        (elec_gen_fossil_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) AS fossil_share_2010,
        CASE 
            WHEN (elec_gen_fossil_twh / (elec_gen_fossil_twh + elec_gen_clean_twh)) > 0.50 THEN 'High Intensity (Dirty)'
            ELSE 'Low Intensity (Clean)'
        END AS cohort_group
    FROM eu_energy_panel
    WHERE year = 2010
),
GenerationComparison AS (
    -- Step 2: Join the cohorts to the 2010 and 2022 actual generation data
    SELECT 
        b.cohort_group,
        SUM(CASE WHEN e.year = 2010 THEN e.elec_gen_fossil_twh ELSE 0 END) AS total_fossil_2010,
        SUM(CASE WHEN e.year = 2022 THEN e.elec_gen_fossil_twh ELSE 0 END) AS total_fossil_2022
    FROM eu_energy_panel e
    JOIN Baseline2010 b ON e.country_name = b.country_name
    WHERE e.year IN (2010, 2022)
    GROUP BY b.cohort_group
)
-- Step 3: Calculate the percentage collapse of fossil fuels per cohort
SELECT 
    cohort_group,
    ROUND(total_fossil_2010, 2) AS starting_fossil_twh_2010,
    ROUND(total_fossil_2022, 2) AS ending_fossil_twh_2022,
    ROUND(((total_fossil_2022 - total_fossil_2010) / total_fossil_2010) * 100, 2) AS fossil_reduction_pct
FROM GenerationComparison
ORDER BY fossil_reduction_pct ASC;



