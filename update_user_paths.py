import asyncio
from pathlib import Path
from storage import UserStorage  

async def update_user_paths():
    user_storage = UserStorage()
    store = await user_storage.read()  # Read existing data
    updated_store = {}

    for username, old_path in store.items():
        # Assume the new path should be in a directory 'known_users' in the same directory as this script
        new_path = Path(__file__).parent / 'known_users' / username.strip() / 'img.jpg'
        updated_store[username] = str(new_path)  # Convert Path object to string for storage

    # Save the updated paths back to the storage
    await user_storage.write(updated_store)

# Run the update function
asyncio.run(update_user_paths())
