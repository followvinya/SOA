import grpc
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, '/app')

from statistics_service.generated import statistics_pb2
from statistics_service.generated import statistics_pb2_grpc
from .clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)


class StatisticsServicer(statistics_pb2_grpc.StatisticsServiceServicer):
    def __init__(self, clickhouse_client: ClickHouseClient):
        self.clickhouse_client = clickhouse_client

    def GetPostStats(self, request, context):
        """Получаем статистику по посту"""
        try:
            stats = self.clickhouse_client.get_post_stats(request.post_id)

            return statistics_pb2.PostStatsResponse(
                post_id=request.post_id,
                views_count=stats['views_count'],
                likes_count=stats['likes_count'],
                comments_count=stats['comments_count']
            )
        except Exception as e:
            logger.error(f"Error getting post stats: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting post stats: {str(e)}")
            return statistics_pb2.PostStatsResponse()

    def GetPostViewsDynamics(self, request, context):
        """Получаем динамику просмотров"""
        try:
            dynamics = self.clickhouse_client.get_post_dynamics(
                post_id=request.post_id,
                event_type='view',
                start_date=request.start_date,
                end_date=request.end_date
            )

            response = statistics_pb2.PostDynamicsResponse()
            for item in dynamics:
                daily_stat = statistics_pb2.DailyStats(
                    date=item['date'],
                    count=item['count']
                )
                response.daily_stats.append(daily_stat)

            return response
        except Exception as e:
            logger.error(f"Error getting views dynamics: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting views dynamics: {str(e)}")
            return statistics_pb2.PostDynamicsResponse()

    def GetPostLikesDynamics(self, request, context):
        """Получаем динамику лайков"""
        try:
            dynamics = self.clickhouse_client.get_post_dynamics(
                post_id=request.post_id,
                event_type='like',
                start_date=request.start_date,
                end_date=request.end_date
            )

            response = statistics_pb2.PostDynamicsResponse()
            for item in dynamics:
                daily_stat = statistics_pb2.DailyStats(
                    date=item['date'],
                    count=item['count']
                )
                response.daily_stats.append(daily_stat)

            return response
        except Exception as e:
            logger.error(f"Error getting likes dynamics: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting likes dynamics: {str(e)}")
            return statistics_pb2.PostDynamicsResponse()

    def GetPostCommentsDynamics(self, request, context):
        """Получаем динамику комментариев"""
        try:
            dynamics = self.clickhouse_client.get_post_dynamics(
                post_id=request.post_id,
                event_type='comment',
                start_date=request.start_date,
                end_date=request.end_date
            )

            response = statistics_pb2.PostDynamicsResponse()
            for item in dynamics:
                daily_stat = statistics_pb2.DailyStats(
                    date=item['date'],
                    count=item['count']
                )
                response.daily_stats.append(daily_stat)

            return response
        except Exception as e:
            logger.error(f"Error getting comments dynamics: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting comments dynamics: {str(e)}")
            return statistics_pb2.PostDynamicsResponse()

    def GetTopPosts(self, request, context):
        """Получаем топ постов"""
        try:
            limit = request.limit if request.limit > 0 else 10
            top_posts = self.clickhouse_client.get_top_posts(
                metric_type=request.metric_type,
                limit=limit
            )

            response = statistics_pb2.TopPostsResponse()
            for item in top_posts:
                top_post = statistics_pb2.TopPost(
                    post_id=item['post_id'],
                    count=item['count']
                )
                response.posts.append(top_post)

            return response
        except Exception as e:
            logger.error(f"Error getting top posts: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting top posts: {str(e)}")
            return statistics_pb2.TopPostsResponse()

    def GetTopUsers(self, request, context):
        """Получаем топ пользователей"""
        try:
            limit = request.limit if request.limit > 0 else 10
            top_users = self.clickhouse_client.get_top_users(
                metric_type=request.metric_type,
                limit=limit
            )

            response = statistics_pb2.TopUsersResponse()
            for item in top_users:
                top_user = statistics_pb2.TopUser(
                    user_id=item['user_id'],
                    count=item['count']
                )
                response.users.append(top_user)

            return response
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting top users: {str(e)}")
            return statistics_pb2.TopUsersResponse()