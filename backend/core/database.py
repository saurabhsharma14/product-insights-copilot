import asyncpg
import os
from contextlib import asynccontextmanager

from core.config import settings

async def get_db_connection():
    # Connect to PostgreSQL using the database_url from settings
    conn = await asyncpg.connect(settings.database_url)
    return conn

@asynccontextmanager
async def get_db():
    conn = await get_db_connection()
    try:
        yield conn
    finally:
        await conn.close()

async def init_db():
    conn = await get_db_connection()
    try:
        await conn.execute('''
        -- Reviews table
        CREATE TABLE IF NOT EXISTS reviews (
            review_id       TEXT PRIMARY KEY,
            review_text     TEXT NOT NULL,
            rating          INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review_date     TEXT NOT NULL,          -- ISO 8601
            app_version     TEXT DEFAULT '',
            developer_reply TEXT DEFAULT '',
            source          TEXT DEFAULT 'Google Play',
            source_url      TEXT DEFAULT '',
            -- Classification (populated after analysis)
            primary_theme   TEXT DEFAULT NULL,
            secondary_theme TEXT DEFAULT NULL,
            sentiment       TEXT DEFAULT NULL,      -- Positive / Neutral / Negative
            severity        TEXT DEFAULT NULL,
            issue_type      TEXT DEFAULT NULL,      -- Complaint / Question / Feature request / Praise / General
            -- Metadata
            batch_id        TEXT NOT NULL,          -- Links reviews to a specific fetch run
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Themes table
        CREATE TABLE IF NOT EXISTS themes (
            id              SERIAL PRIMARY KEY,
            batch_id        TEXT NOT NULL,
            theme_name      TEXT NOT NULL,
            description     TEXT NOT NULL,
            review_count    INTEGER NOT NULL,
            percentage      REAL NOT NULL,
            negative_count  INTEGER NOT NULL,
            avg_rating      REAL NOT NULL,
            trend           TEXT DEFAULT 'Stable',  -- Increasing / Decreasing / Stable / Spiking
            rank_score      REAL NOT NULL,
            rank_position   INTEGER DEFAULT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Fee issues table
        CREATE TABLE IF NOT EXISTS fee_issues (
            id                  SERIAL PRIMARY KEY,
            batch_id            TEXT NOT NULL,
            fee_name            TEXT NOT NULL,
            related_review_count INTEGER NOT NULL,
            share_of_corpus     REAL NOT NULL,
            observed_misunderstanding TEXT NOT NULL,
            confidence          TEXT NOT NULL,       -- High / Medium / Low
            selection_reason    TEXT NOT NULL,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Official sources table
        CREATE TABLE IF NOT EXISTS official_sources (
            id              SERIAL PRIMARY KEY,
            fee_issue_id    INTEGER REFERENCES fee_issues(id),
            url             TEXT NOT NULL,
            title           TEXT NOT NULL,
            domain          TEXT NOT NULL,
            extracted_info  TEXT NOT NULL,
            date_checked    TEXT NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Analysis runs table
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id              SERIAL PRIMARY KEY,
            batch_id        TEXT UNIQUE NOT NULL,
            status          TEXT DEFAULT 'pending',  -- pending / running / completed / failed
            review_count    INTEGER DEFAULT 0,
            review_period_start TEXT,
            review_period_end   TEXT,
            avg_rating      REAL DEFAULT 0,
            themes          TEXT DEFAULT NULL,
            fee_issues      TEXT DEFAULT NULL,
            product_pulse   TEXT DEFAULT NULL,       -- Generated pulse text
            fee_explainer   TEXT DEFAULT NULL,       -- Generated explainer JSON
            approval_status TEXT DEFAULT 'pending',  -- pending / approved / rejected
            approved_at     TEXT DEFAULT NULL,
            mcp_document_status TEXT DEFAULT NULL,   -- success / failed / null
            mcp_gmail_status    TEXT DEFAULT NULL,   -- success / failed / null
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
    finally:
        await conn.close()
