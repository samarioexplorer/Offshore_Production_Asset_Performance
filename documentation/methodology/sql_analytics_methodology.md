\# SQL Analytics Methodology



\## Offshore Production Asset Performance



\*\*Phase:\*\* 5D.4 — SQL Methodology Documentation

\*\*Database:\*\* `offshore\_production\_asset\_performance.db`

\*\*Analytical views:\*\* 17

\*\*Status:\*\* Phase 5D.1–5D.3 validated



\---



\# 1. Purpose



This document defines the methodology, business rules, analytical grain, and architectural principles governing the SQL analytics layer of the Offshore Production Asset Performance solution.



The SQL layer converts the validated relational production model into reusable analytical views for downstream Power BI consumption.



The design intentionally separates:



\- data generation

\- data validation

\- relational storage

\- analytical transformation

\- semantic modeling

\- visualization



This separation improves traceability, reproducibility, and maintainability.



\---



\# 2. Analytical Architecture



The overall data architecture is:



```text

Synthetic Data Generation

&#x20;         ↓

Validated CSV Data

&#x20;         ↓

SQLite Staging Tables

&#x20;         ↓

SQLite Core Relational Model

&#x20;         ↓

SQL Analytical Views

&#x20;         ↓

Power BI Semantic Model

&#x20;         ↓

DAX Measures

&#x20;         ↓

Dashboard / Reporting
