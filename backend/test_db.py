import asyncio
import asyncpg
import os

DATABASE_URL = "postgresql://neondb_owner:npg_ovQWx9VtwEy5@ep-rough-wildflower-axnl5eh4-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("SELECT id, batch_id, status, created_at FROM analysis_runs ORDER BY created_at DESC LIMIT 5")
        for row in rows:
            print(dict(row))
    finally:
        await conn.close()

asyncio.run(main())
