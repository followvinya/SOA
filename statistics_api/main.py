from fastapi import FastAPI, HTTPException, Query, Path, Depends
from typing import List, Optional
from datetime import datetime, date
import grpc
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "statistics_service", "generated"))

import statistics_pb2
import statistics_pb2_grpc

from . import schemas

app = FastAPI(title="Statistics API")

STATISTICS_SERVICE_URL = os.getenv("STATISTICS_SERVICE_URL", "statistics-service:50052")


def get_grpc_channel():
    return grpc.insecure_channel(STATISTICS_SERVICE_URL)


@app.get("/statistics/posts/top", response_model=schemas.TopPostsResponse)
async def get_top_posts(
        metric: schemas.MetricType = Query(..., description="Метрика для топа"),
        limit: int = Query(10, ge=1, le=100)
):
    """Получить топ постов по выбранной метрике"""
    try:
        with get_grpc_channel() as channel:
            stub = statistics_pb2_grpc.StatisticsServiceStub(channel)
            request = statistics_pb2.TopRequest(
                metric_type=metric.value,
                limit=limit
            )
            response = stub.GetTopPosts(request)

            return schemas.TopPostsResponse(
                posts=[
                    schemas.TopPost(post_id=post.post_id, count=post.count)
                    for post in response.posts
                ]
            )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")


@app.get("/statistics/users/top", response_model=schemas.TopUsersResponse)
async def get_top_users(
        metric: schemas.MetricType = Query(..., description="Метрика для топа"),
        limit: int = Query(10, ge=1, le=100)
):
    """Получить топ пользователей по выбранной метрике"""
    try:
        with get_grpc_channel() as channel:
            stub = statistics_pb2_grpc.StatisticsServiceStub(channel)
            request = statistics_pb2.TopRequest(
                metric_type=metric.value,
                limit=limit
            )
            response = stub.GetTopUsers(request)

            return schemas.TopUsersResponse(
                users=[
                    schemas.TopUser(user_id=user.user_id, count=user.count)
                    for user in response.users
                ]
            )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")


# ПОТОМ идут маршруты С параметрами пути

@app.get("/statistics/posts/{post_id}", response_model=schemas.PostStatsResponse)
async def get_post_statistics(post_id: int = Path(..., gt=0)):
    """Получить статистику по посту (просмотры, лайки, комментарии)"""
    try:
        with get_grpc_channel() as channel:
            stub = statistics_pb2_grpc.StatisticsServiceStub(channel)
            request = statistics_pb2.PostStatsRequest(post_id=post_id)
            response = stub.GetPostStats(request)

            return schemas.PostStatsResponse(
                post_id=response.post_id,
                views_count=response.views_count,
                likes_count=response.likes_count,
                comments_count=response.comments_count
            )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")


@app.get("/statistics/posts/{post_id}/views/dynamics", response_model=schemas.DynamicsResponse)
async def get_post_views_dynamics(
        post_id: int = Path(..., gt=0),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None)
):
    """Получить динамику просмотров поста по дням"""
    try:
        with get_grpc_channel() as channel:
            stub = statistics_pb2_grpc.StatisticsServiceStub(channel)
            request = statistics_pb2.PostDynamicsRequest(
                post_id=post_id,
                start_date=start_date.isoformat() if start_date else "",
                end_date=end_date.isoformat() if end_date else ""
            )
            response = stub.GetPostViewsDynamics(request)

            return schemas.DynamicsResponse(
                daily_stats=[
                    schemas.DailyStats(date=stat.date, count=stat.count)
                    for stat in response.daily_stats
                ]
            )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")


@app.get("/statistics/posts/{post_id}/likes/dynamics", response_model=schemas.DynamicsResponse)
async def get_post_likes_dynamics(
        post_id: int = Path(..., gt=0),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None)
):
    """Получить динамику лайков поста по дням"""
    try:
        with get_grpc_channel() as channel:
            stub = statistics_pb2_grpc.StatisticsServiceStub(channel)
            request = statistics_pb2.PostDynamicsRequest(
                post_id=post_id,
                start_date=start_date.isoformat() if start_date else "",
                end_date=end_date.isoformat() if end_date else ""
            )
            response = stub.GetPostLikesDynamics(request)

            return schemas.DynamicsResponse(
                daily_stats=[
                    schemas.DailyStats(date=stat.date, count=stat.count)
                    for stat in response.daily_stats
                ]
            )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")


@app.get("/statistics/posts/{post_id}/comments/dynamics", response_model=schemas.DynamicsResponse)
async def get_post_comments_dynamics(
        post_id: int = Path(..., gt=0),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None)
):
    """Получить динамику комментариев поста по дням"""
    try:
        with get_grpc_channel() as channel:
            stub = statistics_pb2_grpc.StatisticsServiceStub(channel)
            request = statistics_pb2.PostDynamicsRequest(
                post_id=post_id,
                start_date=start_date.isoformat() if start_date else "",
                end_date=end_date.isoformat() if end_date else ""
            )
            response = stub.GetPostCommentsDynamics(request)

            return schemas.DynamicsResponse(
                daily_stats=[
                    schemas.DailyStats(date=stat.date, count=stat.count)
                    for stat in response.daily_stats
                ]
            )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")