import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.reviews import run_autonomous_pipeline
from core.database import init_db

async def main():
    await init_db()
    print("Triggering autonomous pipeline...")
    await run_autonomous_pipeline()
    print("Pipeline finished.")
    
if __name__ == "__main__":
    asyncio.run(main())
