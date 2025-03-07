from sqlalchemy.orm import Session
from . import models, schemas, utils
from fastapi import HTTPException, status


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = get_user_by_username(db, username=user.username)  # in case username exists
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")  # in case email exists

    hashed_password = utils.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not utils.verify_password(password, user.hashed_password):
        return False
    return user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email and user_update.email != db_user.email:
        existing_user = get_user_by_email(db, user_update.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user
