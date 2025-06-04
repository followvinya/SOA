import pytest
import grpc
import sys
import os
from datetime import datetime

sys.path.insert(0, '/app')

from statistics_service.generated import statistics_pb2, statistics_pb2_grpc


class TestStatisticsServiceGRPC:

    def test_get_post_stats_success(self, grpc_statistics_channel, clickhouse_client):
        """Test 1: Get post statistics via gRPC"""
        # Insert test data into ClickHouse
        post_id = 123
        test_events = [
            ('view', 1, post_id, None, datetime.now()),
            ('view', 2, post_id, None, datetime.now()),
            ('like', 1, post_id, None, datetime.now()),
            ('comment', 2, post_id, 1, datetime.now()),
        ]

        clickhouse_client.execute(
            """
            INSERT INTO events (event_type, user_id, post_id, comment_id, timestamp) 
            VALUES
            """,
            test_events
        )

        # Test gRPC call
        stub = statistics_pb2_grpc.StatisticsServiceStub(grpc_statistics_channel)
        request = statistics_pb2.PostStatsRequest(post_id=post_id)
        response = stub.GetPostStats(request)

        # Verify response
        assert response.post_id == post_id
        assert response.views_count == 2
        assert response.likes_count == 1
        assert response.comments_count == 1

    def test_get_top_posts_success(self, grpc_statistics_channel, clickhouse_client):
        """Test 2: Get top posts by metric via gRPC"""
        # Insert test data for multiple posts
        test_events = [
            ('like', 1, 100, None, datetime.now()),
            ('like', 2, 100, None, datetime.now()),
            ('like', 3, 100, None, datetime.now()),
            ('like', 1, 101, None, datetime.now()),
            ('like', 2, 101, None, datetime.now()),
            ('like', 1, 102, None, datetime.now()),
        ]

        clickhouse_client.execute(
            """
            INSERT INTO events (event_type, user_id, post_id, comment_id, timestamp) 
            VALUES
            """,
            test_events
        )

        # Test gRPC call
        stub = statistics_pb2_grpc.StatisticsServiceStub(grpc_statistics_channel)
        request = statistics_pb2.TopRequest(
            metric_type="likes",
            limit=3
        )
        response = stub.GetTopPosts(request)

        # Verify response
        assert len(response.posts) <= 3
        # Posts should be ordered by likes count (descending)
        if len(response.posts) >= 2:
            assert response.posts[0].count >= response.posts[1].count

        # Check that post 100 has most likes (3)
        top_post = next((p for p in response.posts if p.post_id == 100), None)
        assert top_post is not None
        assert top_post.count == 3

    def test_get_post_dynamics_success(self, grpc_statistics_channel, clickhouse_client):
        """Test 3: Get post views dynamics via gRPC"""
        # Insert test data with specific dates
        post_id = 200
        test_events = [
            ('view', 1, post_id, None, datetime(2024, 1, 1, 10, 0)),
            ('view', 2, post_id, None, datetime(2024, 1, 1, 11, 0)),
            ('view', 3, post_id, None, datetime(2024, 1, 2, 10, 0)),
        ]

        clickhouse_client.execute(
            """
            INSERT INTO events (event_type, user_id, post_id, comment_id, timestamp) 
            VALUES
            """,
            test_events
        )

        # Test gRPC call
        stub = statistics_pb2_grpc.StatisticsServiceStub(grpc_statistics_channel)
        request = statistics_pb2.PostDynamicsRequest(
            post_id=post_id,
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
        response = stub.GetPostViewsDynamics(request)

        # Verify response
        assert len(response.daily_stats) >= 1

        # Check specific dates
        jan_1_stats = next((s for s in response.daily_stats if s.date == "2024-01-01"), None)
        jan_2_stats = next((s for s in response.daily_stats if s.date == "2024-01-02"), None)

        if jan_1_stats:
            assert jan_1_stats.count == 2
        if jan_2_stats:
            assert jan_2_stats.count == 1