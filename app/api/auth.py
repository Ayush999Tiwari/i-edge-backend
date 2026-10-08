import secrets
from urllib.parse import urlencode

import httpx

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_REDIRECT_URI,
    FRONTEND_URL,
)

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.database import get_db
from app.models import User

from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


# ==========================================================
# HELPERS
# ==========================================================

def normalize_phone(phone: str) -> str:
    phone = phone.strip()

    if phone.startswith("+"):
        return "+" + "".join(c for c in phone[1:] if c.isdigit())

    return "".join(c for c in phone if c.isdigit())


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user_token(user: User) -> dict:
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


def find_user_by_identifier(
    db: Session,
    identifier: str,
):
    identifier = identifier.strip()

    if "@" in identifier:
        email = normalize_email(identifier)

        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    phone = normalize_phone(identifier)

    return (
        db.query(User)
        .filter(User.phone_number == phone)
        .first()
    )


# ==========================================================
# REGISTER
# ==========================================================

@router.post(
    "/register",
    response_model=TokenResponse,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = (
        normalize_email(request.email)
        if request.email
        else None
    )

    phone = (
        normalize_phone(request.phone_number)
        if request.phone_number
        else None
    )

    # ------------------------------------------------------
    # Must provide either email or phone
    # ------------------------------------------------------

    if not email and not phone:
        raise HTTPException(
            status_code=400,
            detail="Email or phone number is required.",
        )

    # ------------------------------------------------------
    # Check email uniqueness
    # ------------------------------------------------------

    if email:
        existing_email = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )

    # ------------------------------------------------------
    # Check phone uniqueness
    # ------------------------------------------------------

    if phone:
        existing_phone = (
            db.query(User)
            .filter(User.phone_number == phone)
            .first()
        )

        if existing_phone:
            raise HTTPException(
                status_code=409,
                detail="An account with this phone number already exists.",
            )

    # ------------------------------------------------------
    # Create user
    # ------------------------------------------------------

    user = User(
        full_name=request.full_name.strip(),
        email=email,
        phone_number=phone,
        password_hash=hash_password(request.password),
        auth_provider="password",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return create_user_token(user)


# ==========================================================
# LOGIN
# ==========================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = find_user_by_identifier(
        db,
        credentials.identifier,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email/phone or password.",
        )

    # ------------------------------------------------------
    # Verify password
    #
    # Login method is not locked to the provider that created
    # the account. If a password exists, manual login is allowed
    # regardless of whether the account was created with Google,
    # GitHub, or password registration.
    # ------------------------------------------------------

    if not user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="Password login is not set up for this account. Please use Google or GitHub login, or set a password first.",
        )

    if not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email/phone or password.",
        )

    return create_user_token(user)


# ==========================================================
# GOOGLE LOGIN
# ==========================================================

@router.get("/google")
def google_login():

    state = secrets.token_urlsafe(32)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(params)
    )

    return RedirectResponse(url)


# ==========================================================
# GOOGLE CALLBACK
# ==========================================================

@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Google authorization code missing.",
        )

    print("\n========== GOOGLE OAUTH CALLBACK ==========")
    print("Google authorization code received:", bool(code))
    print("Google state received:", bool(state))
    print("===========================================")

    async with httpx.AsyncClient() as client:

        # --------------------------------------------------
        # Exchange authorization code for Google token
        # --------------------------------------------------

        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )

        if token_response.status_code != 200:

            print("\n========== GOOGLE TOKEN ERROR ==========")
            print("STATUS:", token_response.status_code)
            print("RESPONSE:", token_response.text)
            print("========================================\n")

            raise HTTPException(
                status_code=400,
                detail="Google authentication failed.",
            )

        tokens = token_response.json()

        access_token = tokens.get("access_token")

        print(
            "GOOGLE ACCESS TOKEN RECEIVED:",
            bool(access_token),
        )

        if not access_token:
            print("Google token response:", tokens)

            raise HTTPException(
                status_code=400,
                detail="Google access token was not returned.",
            )

        # --------------------------------------------------
        # Get Google user profile
        # --------------------------------------------------

        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        if user_response.status_code != 200:

            print("\n========== GOOGLE PROFILE ERROR ==========")
            print("STATUS:", user_response.status_code)
            print("RESPONSE:", user_response.text)
            print("==========================================\n")

            raise HTTPException(
                status_code=400,
                detail="Unable to retrieve Google profile.",
            )

        profile = user_response.json()

    # ------------------------------------------------------
    # Extract Google profile
    # ------------------------------------------------------

    google_id = profile.get("sub")
    email = profile.get("email")
    name = profile.get("name") or "Google User"

    if not google_id:
        raise HTTPException(
            status_code=400,
            detail="Google account ID was not returned.",
        )

    if email:
        email = normalize_email(email)

    print("\n========== GOOGLE PROFILE ==========")
    print("Google ID received:", bool(google_id))
    print("Email received:", bool(email))
    print("Name:", name)
    print("====================================\n")

    # ------------------------------------------------------
    # First find existing Google account
    # ------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.auth_provider == "google",
            User.provider_id == google_id,
        )
        .first()
    )

    # ------------------------------------------------------
    # If no Google account exists, check email
    # ------------------------------------------------------

    if not user and email:

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    # ------------------------------------------------------
    # Create new Google user
    # ------------------------------------------------------

    if not user:

        user = User(
            full_name=name,
            email=email,
            phone_number=None,
            password_hash=None,
            auth_provider="google",
            provider_id=google_id,
        )

        db.add(user)

        print("Created new Google user.")

    else:

        # --------------------------------------------------
        # IMPORTANT:
        # Do NOT overwrite password authentication.
        #
        # If this email already belongs to a password user,
        # keep auth_provider=password.
        # --------------------------------------------------

        if user.auth_provider == "password":

            print(
                "Existing password account found for Google email."
            )

            # We keep the existing password account.
            # Google provider is not attached here.

        else:

            user.auth_provider = "google"
            user.provider_id = google_id

            print("Existing Google user found.")

    db.commit()
    db.refresh(user)

    # ------------------------------------------------------
    # Create application JWT
    # ------------------------------------------------------

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
        }
    )

    # ------------------------------------------------------
    # Redirect frontend
    # ------------------------------------------------------

    return RedirectResponse(
        f"{FRONTEND_URL}/auth/callback?"
        + urlencode({"token": token})
    )


# ==========================================================
# GITHUB LOGIN
# ==========================================================

@router.get("/github")
def github_login():

    state = secrets.token_urlsafe(32)

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }

    url = (
        "https://github.com/login/oauth/authorize?"
        + urlencode(params)
    )

    return RedirectResponse(url)


# ==========================================================
# GITHUB CALLBACK
# ==========================================================

@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):

    if not code:
        raise HTTPException(
            status_code=400,
            detail="GitHub authorization code missing.",
        )

    print("\n========== GITHUB OAUTH CALLBACK ==========")
    print("GitHub authorization code received:", bool(code))
    print("GitHub state received:", bool(state))
    print("============================================")

    async with httpx.AsyncClient() as client:

        # --------------------------------------------------
        # Exchange GitHub authorization code for token
        # --------------------------------------------------

        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
            headers={
                "Accept": "application/json",
            },
        )

        if token_response.status_code != 200:

            print("\n========== GITHUB TOKEN ERROR ==========")
            print("STATUS:", token_response.status_code)
            print("RESPONSE:", token_response.text)
            print("========================================\n")

            raise HTTPException(
                status_code=400,
                detail="GitHub authentication failed.",
            )

        tokens = token_response.json()

        access_token = tokens.get("access_token")

        print(
            "GITHUB ACCESS TOKEN RECEIVED:",
            bool(access_token),
        )

        if not access_token:

            print("GitHub token response:", tokens)

            raise HTTPException(
                status_code=400,
                detail="GitHub access token was not returned.",
            )

        # --------------------------------------------------
        # Get GitHub user profile
        # --------------------------------------------------

        github_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        if github_response.status_code != 200:

            print("\n========== GITHUB PROFILE ERROR ==========")
            print("STATUS:", github_response.status_code)
            print("RESPONSE:", github_response.text)
            print("==========================================\n")

            raise HTTPException(
                status_code=400,
                detail="Unable to retrieve GitHub profile.",
            )

        profile = github_response.json()

        github_id = str(profile["id"])

        name = profile.get("name") or profile.get(
            "login",
            "GitHub User",
        )

        email = profile.get("email")

        # --------------------------------------------------
        # GitHub may not return email in /user
        # --------------------------------------------------

        if not email:

            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )

            if emails_response.status_code == 200:

                emails = emails_response.json()

                primary = next(
                    (
                        item
                        for item in emails
                        if item.get("primary")
                        and item.get("verified")
                    ),
                    None,
                )

                if primary:
                    email = primary.get("email")

    # ------------------------------------------------------
    # Normalize email
    # ------------------------------------------------------

    if email:
        email = normalize_email(email)

    print("\n========== GITHUB PROFILE ==========")
    print("GitHub ID received:", bool(github_id))
    print("Email received:", bool(email))
    print("Name:", name)
    print("====================================\n")

    # ------------------------------------------------------
    # Find existing GitHub account
    # ------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.auth_provider == "github",
            User.provider_id == github_id,
        )
        .first()
    )

    # ------------------------------------------------------
    # If no GitHub account exists, search by email
    # ------------------------------------------------------

    if not user and email:

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    # ------------------------------------------------------
    # Create new GitHub user
    # ------------------------------------------------------

    if not user:

        user = User(
            full_name=name,
            email=email,
            phone_number=None,
            password_hash=None,
            auth_provider="github",
            provider_id=github_id,
        )

        db.add(user)

        print("Created new GitHub user.")

    else:

        # --------------------------------------------------
        # Do NOT overwrite password authentication
        # --------------------------------------------------

        if user.auth_provider == "password":

            print(
                "Existing password account found for GitHub email."
            )

            # Keep password authentication unchanged.

        else:

            user.auth_provider = "github"
            user.provider_id = github_id

            print("Existing GitHub user found.")

    db.commit()
    db.refresh(user)

    # ------------------------------------------------------
    # Create application JWT
    # ------------------------------------------------------

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
        }
    )

    # ------------------------------------------------------
    # Redirect frontend
    # ------------------------------------------------------

    return RedirectResponse(
        f"{FRONTEND_URL}/auth/callback?"
        + urlencode({"token": token})
    )
