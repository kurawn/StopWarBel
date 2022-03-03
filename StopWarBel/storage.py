from os import getenv
from bot_storage.storage import RedisStorage

storage = RedisStorage(
    host=getenv('REDIS_HOST', 'localhost'),
    username=getenv('REDIS_USER', None),
    password=getenv('REDIS_PASSWORD', None)
)