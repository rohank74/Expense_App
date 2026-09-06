from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User


class DuplicateEmailError(ValueError):
    pass


def register_user(data):
    if User.query.filter_by(email=data.email).first() is not None:
        raise DuplicateEmailError

    user = User(name=data.name, email=data.email, password_hash="")
    user.set_password(data.password)
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise DuplicateEmailError from error

    return user


def authenticate_user(data):
    user = User.query.filter_by(email=data.email).first()
    if user is None or not user.check_password(data.password):
        return None
    return user
