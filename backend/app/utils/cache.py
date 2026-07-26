import json

from redis import Redis
from redis.exceptions import RedisError

from app.config import settings


redis_cache = Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_cache(key: str):
    try:
        value = redis_cache.get(key)
    except RedisError:
        return None
    if not value:
        return None
    return json.loads(value)


def set_cache(key: str, value, ttl: int):
    try:
        redis_cache.setex(key, ttl, json.dumps(value))
    except RedisError:
        return


def delete_cache(key: str):
    try:
        if "*" in key:
            for matched in redis_cache.scan_iter(match=key):
                redis_cache.delete(matched)
            return
        redis_cache.delete(key)
    except RedisError:
        return
