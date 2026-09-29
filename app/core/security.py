# # ==========================================================
# # JWT + password utilities.
# #
# # create_access_token() is moved verbatim from the old auth.py
# # (same algorithm, same expiry logic -- login behavior is unchanged).
# #
# # hash_password / verify_password / decode_access_token are added
# # to satisfy this module's stated responsibilities (hash password,
# # verify password, create access token, verify JWT). Nothing in the
# # original app hashed passwords or verified a bearer token on any
# # route -- login just compares plaintext env credentials, and no
# # endpoint was protected -- so these are additive utilities for
# # future protected routes, not a behavior change to any existing
# # endpoint.
# # ==========================================================
# from datetime import datetime, timedelta, timezone
# from typing import Optional

# from jose import jwt, JWTError
# from passlib.context import CryptContext

# from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# def create_access_token(data: dict) -> str:
#     """Unchanged from the original auth.py create_access_token()."""
#     to_encode = data.copy()
#     expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# def decode_access_token(token: str) -> Optional[dict]:
#     """Verify a JWT issued by create_access_token(). Returns the payload or None."""
#     try:
#         return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#     except JWTError:
#         return None


# def hash_password(plain_password: str) -> str:
#     return _pwd_context.hash(plain_password)


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return _pwd_context.verify(plain_password, hashed_password)






from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def create_access_token(data: dict) -> str:
    payload = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> Optional[dict]:

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        return payload

    except JWTError as e:
        print(
            f"[JWT ERROR] {type(e).__name__}: {e}"
        )

        return None


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return _pwd_context.verify(
        plain_password,
        hashed_password,
    )