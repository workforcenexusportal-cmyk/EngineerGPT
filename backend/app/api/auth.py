"""Authentication & tenancy endpoints: register (creates org), token, profile.

Public signup provisions a new organization and makes the first user its manager
(org owner). OAuth2 / Entra ID / Google federation can plug in here as additional
grant handlers; the local password grant is provided for first-run and self-serve.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.plans import get_limits
from app.core.security import (
    CurrentUser,
    Role,
    TokenData,
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.tenancy import create_organization, get_organization
from app.core.usage import ANALYSIS, document_count, monthly_usage
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)
    company_name: str = Field(default="", max_length=200)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: Role
    org_id: str | None = None
    is_superuser: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PlanInfo(BaseModel):
    key: str
    label: str
    price_usd_month: int
    monthly_analyses: int
    max_documents: int
    max_members: int
    features: list[str]


class UsageInfo(BaseModel):
    analyses_this_month: int
    documents: int


class OrgInfo(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    subscription_status: str | None = None


class ContextResponse(BaseModel):
    user: UserResponse
    organization: OrgInfo | None
    plan: PlanInfo
    usage: UsageInfo


def _issue_token(user: User) -> str:
    return create_access_token(
        TokenData(
            sub=user.id,
            role=user.role,
            org_id=user.org_id,
            is_superuser=user.is_superuser,
        )
    )


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        org_id=user.org_id,
        is_superuser=user.is_superuser,
    )


def _org_info(org: Organization | None) -> OrgInfo | None:
    if org is None:
        return None
    return OrgInfo(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan,
        subscription_status=org.subscription_status,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not settings.allow_public_signup:
        raise HTTPException(status_code=403, detail="Public signup is disabled.")
    existing = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    org_name = body.company_name.strip() or (
        f"{body.full_name.strip()}'s workspace"
        if body.full_name.strip()
        else body.email.split("@")[0]
    )
    org = create_organization(db, name=org_name, commit=False)

    user = User(
        email=body.email,
        full_name=body.full_name.strip(),
        hashed_password=hash_password(body.password),
        # The first member of a new org owns it (manager role).
        role=Role.MANAGER,
        org_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=_issue_token(user), user=_user_response(user))


@router.post("/token", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.execute(select(User).where(User.email == form.username)).scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=_issue_token(user), user=_user_response(user))


@router.get("/me", response_model=TokenData)
def me(current: CurrentUser) -> TokenData:
    return current


@router.get("/context", response_model=ContextResponse)
def context(current: CurrentUser, db: Session = Depends(get_db)) -> ContextResponse:
    """Rich session context for the app shell: identity, org, plan, live usage."""
    user = db.get(User, current.sub)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    org = get_organization(db, current.org_id)
    limits = get_limits(org.plan if org else "free")
    return ContextResponse(
        user=_user_response(user),
        organization=_org_info(org),
        plan=PlanInfo(
            key=limits.key.value,
            label=limits.label,
            price_usd_month=limits.price_usd_month,
            monthly_analyses=limits.monthly_analyses,
            max_documents=limits.max_documents,
            max_members=limits.max_members,
            features=list(limits.features),
        ),
        usage=UsageInfo(
            analyses_this_month=monthly_usage(db, org_id=current.org_id, kind=ANALYSIS),
            documents=document_count(db, org_id=current.org_id),
        ),
    )
