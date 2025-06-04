import pytest
import grpc
import sys
import os

sys.path.insert(0, '/app')

from post_service.generated import posts_pb2, posts_pb2_grpc
from post_service.app.models import Post, PostLike, PostComment


class TestPostServiceGRPC:

    def test_create_post_success(self, grpc_post_channel, post_db_session, sample_post_data):
        """Test 1: Successfully create a post via gRPC"""
        stub = posts_pb2_grpc.PostServiceStub(grpc_post_channel)

        request = posts_pb2.CreatePostRequest(
            title=sample_post_data["title"],
            description=sample_post_data["description"],
            creator_id=sample_post_data["creator_id"],
            is_private=sample_post_data["is_private"],
            tags=sample_post_data["tags"]
        )

        response = stub.CreatePost(request)

        # Verify response
        assert response.id > 0
        assert response.title == sample_post_data["title"]
        assert response.description == sample_post_data["description"]
        assert response.creator_id == sample_post_data["creator_id"]
        assert response.is_private == sample_post_data["is_private"]
        assert list(response.tags) == sample_post_data["tags"]

        # Verify database entry
        db_post = post_db_session.query(Post).filter(Post.id == response.id).first()
        assert db_post is not None
        assert db_post.title == sample_post_data["title"]
        assert db_post.creator_id == sample_post_data["creator_id"]

    def test_like_post_success(self, grpc_post_channel, post_db_session):
        """Test 2: Successfully like a post via gRPC"""
        # First create a post
        stub = posts_pb2_grpc.PostServiceStub(grpc_post_channel)

        create_request = posts_pb2.CreatePostRequest(
            title="Test Post for Like",
            description="Test Description",
            creator_id=1,
            is_private=False,
            tags=[]
        )
        create_response = stub.CreatePost(create_request)
        post_id = create_response.id

        # Now like the post
        like_request = posts_pb2.LikePostRequest(
            post_id=post_id,
            user_id=2
        )
        like_response = stub.LikePost(like_request)

        # Verify response
        assert like_response.success is True
        assert like_response.like_id > 0

        # Verify database entry
        db_like = post_db_session.query(PostLike).filter(
            PostLike.post_id == post_id,
            PostLike.user_id == 2
        ).first()
        assert db_like is not None
        assert db_like.post_id == post_id
        assert db_like.user_id == 2

    def test_add_comment_success(self, grpc_post_channel, post_db_session):
        """Test 3: Successfully add comment to post via gRPC"""
        # First create a post
        stub = posts_pb2_grpc.PostServiceStub(grpc_post_channel)

        create_request = posts_pb2.CreatePostRequest(
            title="Test Post for Comment",
            description="Test Description",
            creator_id=1,
            is_private=False,
            tags=[]
        )
        create_response = stub.CreatePost(create_request)
        post_id = create_response.id

        # Add comment
        comment_text = "This is a test comment"
        comment_request = posts_pb2.AddCommentRequest(
            post_id=post_id,
            user_id=2,
            text=comment_text
        )
        comment_response = stub.AddComment(comment_request)

        # Verify response
        assert comment_response.id > 0
        assert comment_response.post_id == post_id
        assert comment_response.user_id == 2
        assert comment_response.text == comment_text

        # Verify database entry
        db_comment = post_db_session.query(PostComment).filter(
            PostComment.id == comment_response.id
        ).first()
        assert db_comment is not None
        assert db_comment.post_id == post_id
        assert db_comment.user_id == 2
        assert db_comment.text == comment_text