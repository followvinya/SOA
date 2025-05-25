from pydantic import BaseModel
from typing import List
from enum import Enum

class MetricType(str, Enum):
    likes = "likes"
    comments = "comments"
    views = "views"

class PostStatsResponse(BaseModel):
    post_id: int
    views_count: int
    likes_count: int
    comments_count: int

class DailyStats(BaseModel):
    date: str
    count: int

class DynamicsResponse(BaseModel):
    daily_stats: List[DailyStats]

class TopPost(BaseModel):
    post_id: int
    count: int

class TopPostsResponse(BaseModel):
    posts: List[TopPost]

class TopUser(BaseModel):
    user_id: int
    count: int

class TopUsersResponse(BaseModel):
    users: List[TopUser]