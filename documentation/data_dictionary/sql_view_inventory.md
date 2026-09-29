\# SQL Analytical View Inventory



\## Offshore Production Asset Performance



\*\*Phase:\*\* 5D.3 — SQL View Inventory

\*\*Database:\*\* `offshore\_production\_asset\_performance.db`

\*\*Analytical view count:\*\* 17

\*\*Status:\*\* Validated through Phase 5D.2



\---



\## 1. Purpose



This document inventories the analytical SQL views used by the Offshore Production Asset Performance solution.



The analytical SQL layer sits between the relational SQLite model and the downstream Power BI semantic model:



```text

Validated CSV

&#x20;     ↓

SQLite Staging

&#x20;     ↓

SQLite Core Relational Model

&#x20;     ↓

SQL Analytical Views

&#x20;     ↓

Power BI Semantic Model

&#x20;     ↓

DAX

&#x20;     ↓

Dashboard
