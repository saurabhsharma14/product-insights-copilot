import asyncio
from core.database import init_db
from api.reviews import run_autonomous_pipeline

async def main():
    await init_db()
    await run_autonomous_pipeline()

asyncio.run(main())
