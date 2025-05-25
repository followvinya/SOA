from fastapi import FastAPI, Depends, HTTPException, status, Query, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import List, Optional
import grpc
from . import schemas, utils
from .grpc_client import PostServiceClient
import logging
import json

app = FastAPI(title="System API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
post_service = PostServiceClient()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate):
    return await utils.make_request("POST", "/users/", json=user.dict())

@app.post("/login", response_model=schemas.Token)
async def login(user_login: schemas.UserLogin):
    return await utils.make_request("POST", "/login/", json=user_login.dict())

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    data = {
        "username": form_data.username,
        "password": form_data.password
    }
    return await utils.make_request("POST", "/login/", json=data)

@app.get("/users/me", response_model=schemas.UserResponse)
async def get_user_profile(token: str = Depends(oauth2_scheme)):
    headers = {"Authorization": f"Bearer {token}"}
    return await utils.make_request("GET", "/users/me/", headers=headers)


@app.put("/users/me", response_model=schemas.UserResponse)
async def update_user_profile(user_update: schemas.UserUpdate, token: str = Depends(oauth2_scheme)):
    headers = {"Authorization": f"Bearer {token}"}

    update_data = user_update.dict()  # probmlemka s dates byla
    if update_data.get('birth_date'):
        update_data['birth_date'] = update_data['birth_date'].isoformat()

    return await utils.make_request("PUT", "/users/me/", json=update_data, headers=headers)


async def get_user_id_from_token(token: str = Depends(oauth2_scheme)):
    # Get user profile from user service using token
    user_profile = await utils.make_request("GET", "/users/me/", headers={"Authorization": f"Bearer {token}"})
    return user_profile["id"]

# Posts endpoints
@app.post("/posts", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: schemas.PostCreate, user_id: int = Depends(get_user_id_from_token)):
    try:
        return post_service.create_post(
            title=post.title,
            description=post.description,
            creator_id=user_id,
            is_private=post.is_private,
            tags=post.tags
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.INTERNAL:
            raise HTTPException(status_code=500, detail=e.details())
        raise HTTPException(status_code=400, detail=e.details())

@app.get("/posts/{post_id}", response_model=schemas.PostResponse)
async def get_post(post_id: int = Path(..., gt=0), user_id: int = Depends(get_user_id_from_token)):
    try:
        return post_service.get_post(post_id=post_id, user_id=user_id)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        raise HTTPException(status_code=500, detail=e.details())

@app.get("/posts", response_model=schemas.PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = Depends(get_user_id_from_token)
):
    try:
        return post_service.list_posts(user_id=user_id, page=page, page_size=page_size)
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=e.details())

@app.put("/posts/{post_id}", response_model=schemas.PostResponse)
async def update_post(
    post_id: int,
    post_update: schemas.PostUpdate,
    user_id: int = Depends(get_user_id_from_token)
):
    update_data = {k: v for k, v in post_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="At least one field must be provided for update")

    if post_update.title is not None and len(post_update.title) < 1:
        raise HTTPException(status_code=400, detail="Title must not be empty")

    if post_update.description is not None and len(post_update.description) < 1:
        raise HTTPException(status_code=400, detail="Description must not be empty")

    try:
        return post_service.update_post(
            post_id=post_id,
            creator_id=user_id,
            title=post_update.title,
            description=post_update.description,
            is_private=post_update.is_private,
            tags=post_update.tags
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        raise HTTPException(status_code=500, detail=e.details())

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, user_id: int = Depends(get_user_id_from_token)):
    try:
        success = post_service.delete_post(post_id=post_id, creator_id=user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        return {"status": "success"}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        raise HTTPException(status_code=500, detail=e.details())

@app.post("/posts/{post_id}/like", response_model=schemas.LikeResponse)
async def like_post(post_id: int, user_id: int = Depends(get_user_id_from_token)):
    try:
        return post_service.like_post(post_id=post_id, user_id=user_id)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        raise HTTPException(status_code=500, detail=e.details())

@app.post("/posts/{post_id}/view", response_model=schemas.ViewResponse)
async def view_post(post_id: int, user_id: int = Depends(get_user_id_from_token)):
    try:
        return post_service.view_post(post_id=post_id, user_id=user_id)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        raise HTTPException(status_code=500, detail=e.details())

@app.post("/posts/{post_id}/comments", response_model=schemas.CommentResponse)
async def add_comment(
    post_id: int,
    comment: schemas.CommentCreate,
    user_id: int = Depends(get_user_id_from_token)
):
    try:
        return post_service.add_comment(post_id=post_id, user_id=user_id, text=comment.text)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        raise HTTPException(status_code=500, detail=e.details())

@app.get("/posts/{post_id}/comments", response_model=schemas.CommentListResponse)
async def get_post_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = Depends(get_user_id_from_token)
):
    try:
        return post_service.get_post_comments(
            post_id=post_id,
            user_id=user_id,
            page=page,
            page_size=page_size
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Post not found or access denied")
        raise HTTPException(status_code=500, detail=e.details())