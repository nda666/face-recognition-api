import os
import diskcache

CACHE_DIR = os.getenv("CACHE_DIR", os.path.join(os.getcwd(), "storage", "url_cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

# TTL default 5 menit, size limit 500MB
url_cache = diskcache.Cache(CACHE_DIR, size_limit=500 * 1024 * 1024)