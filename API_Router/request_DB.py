import json
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from model_DB import User, Media, WatchHistory, WatchStatus, Episode
from redis_DB import redis_db
