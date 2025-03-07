from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from . import schemas, utils

app = FastAPI(title="System API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate):
    return await utils.make_request("POST", "/users/", json=user.dict())

@app.post("/login/", response_model=schemas.Token)
async def login(user_login: schemas.UserLogin):
    return await utils.make_request("POST", "/login/", json=user_login.dict())

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    data = {
        "username": form_data.username,
        "password": form_data.password
    }
    return await utils.make_request("POST", "/login/", json=data)

@app.get("/users/me/", response_model=schemas.UserResponse)
async def get_user_profile(token: str = Depends(oauth2_scheme)):
    headers = {"Authorization": f"Bearer {token}"}
    return await utils.make_request("GET", "/users/me/", headers=headers)


@app.put("/users/me/", response_model=schemas.UserResponse)
async def update_user_profile(user_update: schemas.UserUpdate, token: str = Depends(oauth2_scheme)):
    headers = {"Authorization": f"Bearer {token}"}

    update_data = user_update.dict()  # probmlemka s dates byla
    if update_data.get('birth_date'):
        update_data['birth_date'] = update_data['birth_date'].isoformat()

    return await utils.make_request("PUT", "/users/me/", json=update_data, headers=headers)