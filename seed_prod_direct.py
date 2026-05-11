import os
import asyncio
from seed import seed

# Force set the DATABASE_URL to the Supabase URL provided by the user.
# We use +asyncpg for the SQLAlchemy async driver.
prod_url = "postgresql+asyncpg://postgres:esabatadnimad1123@db.ntdcygxzezorgivqeawv.supabase.co:5432/postgres"
os.environ["DATABASE_URL"] = prod_url

async def run_seed():
    print(f"Connecting to production database at: {prod_url.split('@')[1]}...")
    try:
        await seed()
        print("\nSUCCESS: Production database has been seeded.")
    except Exception as e:
        print(f"\nFAILURE: Could not seed database: {e}")

if __name__ == "__main__":
    asyncio.run(run_seed())
