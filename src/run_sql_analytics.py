"""
Customer Retention & Revenue Risk Analytics
Module: run_sql_analytics.py

Purpose:
- Execute all SQL queries from `sql/data_quality_checks.sql` and `sql/retention_analysis.sql`.
- Verify queries against SQLite database `data/processed/telco_churn.db`.
- Check data quality assertions (ensure 0 failures).
- Output formatted result tables and persist them to `reports/sql_query_results.txt`.
"""

import sys
import re
import sqlite3
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("sql_runner")

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def split_sql_statements(sql_text: str) -> list[str]:
    """Split SQL file into executable individual statements."""
    # Remove comment blocks and split by semicolon
    statements = []
    current_stmt = []
    for line in sql_text.splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("--"):
            continue
        current_stmt.append(line)
        if clean_line.endswith(";"):
            stmt = "\n".join(current_stmt).strip()
            if stmt:
                statements.append(stmt)
            current_stmt = []
    return statements

def run_data_quality_checks(conn: sqlite3.Connection, project_root: Path) -> str:
    """Run data quality assertions and verify zero defects."""
    dq_file = project_root / "sql" / "data_quality_checks.sql"
    sql_text = dq_file.read_text(encoding="utf-8")
    statements = split_sql_statements(sql_text)
    
    report_lines = ["=" * 80, "SQL DATA QUALITY AUDIT RESULTS", "=" * 80]
    all_passed = True

    for i, stmt in enumerate(statements, start=1):
        df_res = pd.read_sql_query(stmt, conn)
        report_lines.append(f"\n--- Check {i} ---")
        report_lines.append(stmt.strip())
        report_lines.append("\nResult:")
        report_lines.append(df_res.to_string(index=False))
        
        # Validate that check counts are 0
        if df_res.empty:
            report_lines.append("Status: PASSED (0 violating records)")
        else:
            total_violations = df_res.select_dtypes(include="number").sum().sum()
            if total_violations == 0:
                report_lines.append("Status: PASSED (All audit metrics are 0)")
            else:
                report_lines.append(f"Status: WARNING/FAIL (Violations detected: {total_violations})")
                all_passed = False

    logger.info(f"Data Quality Audit Completed. All Checks Passed: {all_passed}")
    return "\n".join(report_lines)

def run_retention_analyses(conn: sqlite3.Connection, project_root: Path) -> str:
    """Execute analytical queries and format output."""
    analysis_file = project_root / "sql" / "retention_analysis.sql"
    sql_text = analysis_file.read_text(encoding="utf-8")
    
    # Extract query blocks with their headers
    query_blocks = re.split(r"--\s*-{5,}\n--\s*QUERY\s+(\d+):\s*([^\n]+)", sql_text)
    
    report_lines = ["=" * 80, "SQL RETENTION & REVENUE RISK ANALYTICAL RESULTS", "=" * 80]

    if len(query_blocks) > 1:
        # Blocks are: [preamble, q_num1, q_title1, content1, q_num2, q_title2, content2, ...]
        idx = 1
        while idx < len(query_blocks):
            q_num = query_blocks[idx].strip()
            q_title = query_blocks[idx + 1].strip()
            q_content = query_blocks[idx + 2].strip()
            idx += 3

            statements = split_sql_statements(q_content)
            for stmt in statements:
                df_res = pd.read_sql_query(stmt, conn)
                report_lines.append(f"\n[QUERY {q_num}: {q_title}]")
                report_lines.append(df_res.to_string(index=False))
                report_lines.append("-" * 80)
    else:
        # Fallback split
        statements = split_sql_statements(sql_text)
        for i, stmt in enumerate(statements, 1):
            df_res = pd.read_sql_query(stmt, conn)
            report_lines.append(f"\n[QUERY {i}]")
            report_lines.append(df_res.to_string(index=False))
            report_lines.append("-" * 80)

    return "\n".join(report_lines)

def main():
    project_root = get_project_root()
    db_path = project_root / "data" / "processed" / "telco_churn.db"
    results_path = project_root / "reports" / "sql_query_results.txt"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Run src/data_cleaning.py first.")

    with sqlite3.connect(db_path) as conn:
        dq_report = run_data_quality_checks(conn, project_root)
        analysis_report = run_retention_analyses(conn, project_root)

        full_report = f"{dq_report}\n\n\n{analysis_report}\n"
        results_path.write_text(full_report, encoding="utf-8")
        logger.info(f"All SQL results successfully written to {results_path}")
        print(full_report)

if __name__ == "__main__":
    main()
