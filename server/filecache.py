import os
import hashlib
import json
import glob

class FileCache:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_file_path(self, url: str) -> str:
        """Generate a file path based on the URL's MD5 hash."""
        file_name = hashlib.md5(url.encode('utf-8')).hexdigest() + '.json'
        return os.path.join(self.cache_dir, file_name)

    def set(self, url: str, key: str, value):
        """
        Store a value under the given key in the cache file for the URL.
        
        Args:
            url (str): The URL serving as the unique key.
            key (str): The property name (e.g., "title", "text").
            value: The JSON-serializable value to store.
        """
        file_path = self._get_file_path(url)
        data = {}
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data['url'] = url  # Always store the URL for reference.
        data[key] = value
        with open(file_path, 'w') as f:
            json.dump(data, f)

    def get(self, url: str, key: str):
        """
        Retrieve a value by key from the cache file for the URL.
        
        Args:
            url (str): The URL serving as the unique key.
            key (str): The property name to retrieve.
        
        Returns:
            The stored value, or None if not found.
        """
        file_path = self._get_file_path(url)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    return data.get(key)
                except json.JSONDecodeError:
                    return None
        return None

    def cleanup(self):
        """Remove all cached files in the cache directory."""
        files = glob.glob(os.path.join(self.cache_dir, '*.json'))
        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"Error removing file {file}: {e}")
