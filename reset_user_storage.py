import shutil
from pathlib import Path

def reset_user_storage():
    # Define paths
    base_path = Path(__file__).parent
    user_storage_directory = base_path / 'known_users'
    storage_data_file = base_path / 'user_storage.dat'
    key_file = base_path / 'encryption.key'
    iv_file = base_path / 'encryption.iv'

    # Remove user storage directory
    if user_storage_directory.exists():
        shutil.rmtree(user_storage_directory)
        print(f"Deleted directory: {user_storage_directory}")

    # Remove data files
    for file in [storage_data_file, key_file, iv_file]:
        if file.exists():
            file.unlink()
            print(f"Deleted file: {file}")

if __name__ == '__main__':
    reset_user_storage()
    print("User storage has been reset.")
