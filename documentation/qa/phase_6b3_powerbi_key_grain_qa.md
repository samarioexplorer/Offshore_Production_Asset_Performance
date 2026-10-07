\# Phase 6B.3B â€” Power BI Key / Grain QA



\## 1. Purpose



This validation establishes that the 12 approved Power BI semantic inputs have the expected row counts, key uniqueness, analytical grain, referential integrity, and date coverage before Power BI relationship implementation.



The validation is performed against the authoritative SQLite database:



`database/offshore\_production\_asset\_performance.db`



No Power BI relationships or DAX measures are modified as part of this QA gate.



\---



\## 2. Semantic Inputs Validated



The following 12 analytical inputs were validated:



\### Dimensions



1\. `Dim\_Date`

2\. `Dim\_Field`

3\. `Dim\_Manifold`

4\. `Dim\_Well`

5\. `Dim\_Equipment`

6\. `Dim\_Failure\_Cause`

7\. `Dim\_Intervention`

8\. `Dim\_Scenario`



\### Core Facts



9\. `Fact\_Production\_Impact\_Daily`

10\. `Fact\_Downtime\_Event`

11\. `Fact\_Intervention\_Event`



\### Economics



12\. `vw\_Economics\_Daily`



`Fact\_Production\_Daily` is intentionally excluded from the Power BI semantic model and remains part of the SQLite engineering layer.



\---



\## 3. Expected Analytical Grain



| Analytical Input               | Expected Grain     | Key                            |

| ------------------------------ | ------------------ | ------------------------------ |

| `Dim\_Date`                     | Date               | `Date`                         |

| `Dim\_Field`                    | Field              | `Field\_ID`                     |

| `Dim\_Manifold`                 | Manifold           | `Manifold\_ID`                  |

| `Dim\_Well`                     | Well               | `Well\_ID`                      |

| `Dim\_Equipment`                | Equipment          | `Equipment\_ID`                 |

| `Dim\_Failure\_Cause`            | Failure Cause      | `Failure\_Cause\_ID`             |

| `Dim\_Intervention`             | Intervention Type  | `Intervention\_Type\_ID`         |

| `Dim\_Scenario`                 | Scenario           | `Scenario\_ID`                  |

| `Fact\_Production\_Impact\_Daily` | Well-Day           | `Date + Well\_ID`               |

| `Fact\_Downtime\_Event`          | Downtime Event     | `Downtime\_ID`                  |

| `Fact\_Intervention\_Event`      | Intervention Event | `Intervention\_ID`              |

| `vw\_Economics\_Daily`           | Well-Day-Scenario  | `Date + Well\_ID + Scenario\_ID` |



\---



\## 4. Expected Row Counts



| Table                          | Expected Rows |

| ------------------------------ | ------------: |

| `Dim\_Date`                     |         1,461 |

| `Dim\_Field`                    |             1 |

| `Dim\_Manifold`                 |             4 |

| `Dim\_Well`                     |            30 |

| `Dim\_Equipment`                |            35 |

| `Dim\_Failure\_Cause`            |            16 |

| `Dim\_Intervention`             |             6 |

| `Dim\_Scenario`                 |             3 |

| `Fact\_Production\_Impact\_Daily` |        32,250 |

| `Fact\_Downtime\_Event`          |           660 |

| `Fact\_Intervention\_Event`      |            39 |

| `vw\_Economics\_Daily`           |        96,750 |



\---



\## 5. QA Results



\### 5.1 Row Count Validation



All 12 semantic inputs matched their expected row counts.



\*\*Result: 12/12 PASS\*\*



\### 5.2 Dimension Key Uniqueness



All eight dimensions were validated for:



\* unique primary/business keys

\* null keys



\*\*Result: 16/16 PASS\*\*



\### 5.3 Fact Grain Validation



The four analytical fact structures were validated against their intended grains.



\#### Production Impact



`Date + Well\_ID`



32,250 unique well-day records.



\*\*Result: PASS\*\*



\#### Downtime



`Downtime\_ID`



660 unique downtime events.



\*\*Result: PASS\*\*



\#### Intervention



`Intervention\_ID`



39 unique intervention events.



\*\*Result: PASS\*\*



\#### Economics



`Date + Well\_ID + Scenario\_ID`



96,750 unique scenario well-day records.



\*\*Result: PASS\*\*



\### 5.4 Referential Integrity



The following relationships were checked for orphan records:



\* `Dim\_Well â†’ Dim\_Field`

\* `Dim\_Well â†’ Dim\_Manifold`

\* `Dim\_Equipment â†’ Dim\_Field`

\* `Fact\_Downtime\_Event â†’ Dim\_Well`

\* `Fact\_Downtime\_Event â†’ Dim\_Equipment`

\* `Fact\_Downtime\_Event â†’ Dim\_Failure\_Cause`

\* `Fact\_Intervention\_Event â†’ Dim\_Well`

\* `Fact\_Intervention\_Event â†’ Dim\_Intervention`

\* `Fact\_Production\_Impact\_Daily â†’ Dim\_Well`

\* `vw\_Economics\_Daily â†’ Dim\_Well`

\* `vw\_Economics\_Daily â†’ Dim\_Scenario`



\*\*Result: 11/11 PASS\*\*



No orphan foreign-key values were identified.



\### 5.5 Date Integrity



The following analytical date relationships were validated against `Dim\_Date`:



\* `Fact\_Production\_Impact\_Daily\[Date]`

\* `Fact\_Downtime\_Event\[Date]`

\* `vw\_Economics\_Daily\[Date]`



All analytical dates were represented in `Dim\_Date`.



\*\*Result: 3/3 PASS\*\*



\---



\## 6. Final QA Summary



| QA Category           | Checks | Passed | Failed |

| --------------------- | -----: | -----: | -----: |

| Row counts            |     12 |     12 |      0 |

| Dimension keys        |     16 |     16 |      0 |

| Fact grain            |      8 |      8 |      0 |

| Referential integrity |     11 |     11 |      0 |

| Date integrity        |      3 |      3 |      0 |

| \*\*Total\*\*             | \*\*50\*\* | \*\*50\*\* |  \*\*0\*\* |



\### Final Status



\*\*POWER BI KEY / GRAIN QA: PASS\*\*



\*\*50 / 50 checks passed\*\*



\*\*0 failed\*\*



\---



\## 7. QA Interpretation



The semantic source layer satisfies the structural requirements for Power BI relationship implementation.



The validation confirms:



\* dimension keys are unique and non-null;

\* fact grains are explicitly defined and unique;

\* expected row counts are reconciled;

\* foreign-key references contain no orphan values;

\* analytical dates are covered by the authoritative date dimension;

\* economics data preserves the intended `Date Ã— Well Ã— Scenario` grain;

\* no additional summary views are required as independent Power BI semantic tables.



\---



\## 8. Relationship Implementation Gate



Following successful completion of Phase 6B.3B, the model is approved to proceed to:



\*\*Phase 6B.4 â€” Power BI Relationship Implementation\*\*



The intended relationship design is:



\* one-to-many relationships;

\* dimension-to-fact filtering;

\* single-direction filtering;

\* no direct fact-to-fact relationships;

\* `Dim\_Date` as the authoritative date dimension;

\* `Dim\_Scenario` filtering `vw\_Economics\_Daily`;

\* `Dim\_Well` acting as the principal conformed operational dimension.



No DAX measures or dashboard visuals are part of this QA gate.



\---



\## 9. Validation Script



The QA was executed using:



`python/validation/validate\_powerbi\_keys\_grain.py`



Execution command:



```powershell

python python\\validation\\validate\_powerbi\_keys\_grain.py

```



Final execution result:



```text

TOTAL CHECKS : 50

PASSED       : 50

FAILED       : 0

POWER BI KEY / GRAIN QA STATUS: PASS

```



\---



\## 10. Phase Status



\*\*Phase 6B.3B â€” COMPLETE\*\*



\*\*Status: PASS\*\*



\*\*Next phase: Phase 6B.4 â€” Relationship Implementation\*\*
