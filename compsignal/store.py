"""DuckDB storage: one file, two tables, easy to query with plain SQL."""
import datetime as dt
import os

import duckdb

DB_PATH = os.environ.get("COMPSIGNAL_DB", "data/compsignal.duckdb")


def connect(path=None):
    path = path or DB_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = duckdb.connect(path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            company VARCHAR, source VARCHAR, job_id VARCHAR, title VARCHAR,
            location VARCHAR, url VARCHAR, text VARCHAR,
            first_seen DATE, last_seen DATE,
            PRIMARY KEY (company, job_id)
        )"""
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            company VARCHAR PRIMARY KEY, source VARCHAR, n_jobs INTEGER, last_collected DATE
        )"""
    )
    return con


def save_company(con, company, source, jobs, today=None):
    today = today or dt.date.today()
    for j in jobs:
        con.execute(
            """
            INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT (company, job_id) DO UPDATE SET
              title=excluded.title, location=excluded.location, url=excluded.url,
              text=excluded.text, last_seen=excluded.last_seen""",
            [company, source, j["job_id"], j["title"], j["location"], j["url"], j["text"], today, today],
        )
    con.execute(
        """
        INSERT INTO companies VALUES (?,?,?,?)
        ON CONFLICT (company) DO UPDATE SET
          source=excluded.source, n_jobs=excluded.n_jobs, last_collected=excluded.last_collected""",
        [company, source, len(jobs), today],
    )


def current_jobs(con, company):
    """Postings still open at the company's latest collection."""
    rows = con.execute(
        """
        SELECT j.title, j.text, j.url, j.location, j.first_seen
        FROM jobs j JOIN companies c USING (company)
        WHERE j.company = ? AND j.last_seen = c.last_collected""",
        [company],
    ).fetchall()
    return [
        {"title": t, "text": x, "url": u, "location": loc, "first_seen": fs}
        for t, x, u, loc, fs in rows
    ]


def collected_companies(con):
    return [r[0] for r in con.execute("SELECT company FROM companies ORDER BY company").fetchall()]
