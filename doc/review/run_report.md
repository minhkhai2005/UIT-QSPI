# Run report — UIT QSPI specification review, 2026-11-18

## Input
- Reviewed: `rtl/qspi/doc/UIT_QSPI_Specification.md` (HDS V2.0, sha256 8cbfcfcf…57cbb), all 1541 lines.
- Folder: 26 figures in `doc/images/`. `lint/`, `logical/`, `sim/` and `syn/` hold only `.gitkeep`. The cited `sdc/m_uit_qspi_wrap.sdc`, REF-008 and UIT-Tesla-QSPI-SPEC v0.2 are not present.
- Review list: 17 items, confirmed by the user before the deep analysis (step 5).

## Steps and results
| Step | Command / action | Result |
|---|---|---|
| 2 | `vlsit_find_python.sh` | /usr/bin/python3 |
| 4 | `vlsit_spec_inventory.py` | 47 sections, 64 tables, 0 REQ, 0 TEST, 14 open items, 18 DEC |
| 6 | Standards compliance | table in REVIEW chapter 6 (APB IHI 0024E, AHB IHI 0033C, SPI NOR de facto) |
| 7 | Web search (4 queries) | STM32 QUADSPI, DesignWare SSI, Cadence/ADI/Arasan xSPI, flash tCLQV; sources dated 2026-11-18 |
| 9 | `vlsit_scorecard.py` | `RESULT: PASS (weighted 2.98, verdict Conditional)` |
| 10 | `vlsit_report_check.py REVIEW_UIT_QSPI.md` | `RESULT: PASS (0 errors, 0 warnings)`, 24 findings |
| final | `vlsit_review_report.py check vlsit_spec_2026-11-18.md` | `RESULT: PASS`, fix 19, waive 5 |
| gate | `vlsit_review_gate.py metrics` | `RESULT: FAIL`: 1 unwaived Critical (F-001); waivers 5/10; sampling 100 % |
| gate | `sample` / `group` | 3 sampled (F-003, F-009, F-010, all tp); 14 root-cause groups |

## Gaps and how they were handled
- No RTL or tool evidence: the RTL fixes are proposals written from the specification. Each is labelled INFERENCE where it depends on reasoning.
- Gate FAIL is kept: the Blocker needs an RTL change, and waiving it would hide the main result.
- `vlsit_report_check.py` writes findings without verdict or root cause, but `vlsit_review_gate.py` needs both. `review_data.py` therefore emits a separate `gate_findings.json` from the same finding list, and the skill scripts were not changed.
- The audit is a self-audit because no second reviewer was available.
- Market rows without a dated source are labelled `INFERENCE (no external source)`. Only the STM32 register layout row is labelled this way.

## Rule check
R-001 (folder inventory, appendix), R-002/R-003/R-012/R-013/R-014 (both scripts PASS), R-004/R-015 (chapter 19 source column), R-005 (clause numbers not read are not cited), R-006 (list confirmed by user), R-007 (chapter 9), R-008 (proxy labelled), R-009 (performance table, unquantified flagged), R-010 (chapter 13), R-011 (seven domain chapters, each with a finding), R-016 (new folder, nothing overwritten), R-019 (dated report PASS), R-020 (gate RESULT quoted), R-021 (audit table), R-022 (24 traced, 0 aggregated).
