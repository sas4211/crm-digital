import os
from dotenv import load_dotenv
import asyncio

# Load the production environment variables and FORCE override any local .env values
load_dotenv(".env.production", override=True)

db_url = os.getenv('DATABASE_URL')
print(f"DEBUG: Process DATABASE_URL is: {db_url[:30]}...")

from seed import seed

if __name__ == "__main__":
    if not db_url or "localhost" in db_url:
        print("CRITICAL ERROR: DATABASE_URL is still pointing to localhost or is empty!")
    else:
        asyncio.run(seed())
