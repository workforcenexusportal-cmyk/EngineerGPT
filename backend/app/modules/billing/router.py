"""Billing HTTP surface: plans catalog, checkout, portal, and Stripe webhook."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.plans import PLANS, Plan
from app.core.security import CurrentUser, Role, require_role
from app.core.tenancy import get_organization
from app.models.user import User
from app.modules.billing import service

router = APIRouter(prefix="/billing", tags=["Billing"])


class PlanCatalogItem(BaseModel):
    key: str
    label: str
    price_usd_month: int
    monthly_analyses: int
    max_documents: int
    max_members: int
    features: list[str]
    purchasable: bool


class CheckoutRequest(BaseModel):
    plan: Plan


class RedirectResponse(BaseModel):
    url: str


@router.get("/plans", response_model=list[PlanCatalogItem])
def list_plans() -> list[PlanCatalogItem]:
    """Public plan catalog for pricing pages."""
    items: list[PlanCatalogItem] = []
    for limits in PLANS.values():
        purchasable = limits.key is not Plan.FREE and settings.billing_enabled
        items.append(
            PlanCatalogItem(
                key=limits.key.value,
                label=limits.label,
                price_usd_month=limits.price_usd_month,
                monthly_analyses=limits.monthly_analyses,
                max_documents=limits.max_documents,
                max_members=limits.max_members,
                features=list(limits.features),
                purchasable=purchasable,
            )
        )
    return items


@router.post("/checkout", response_model=RedirectResponse)
def checkout(
    body: CheckoutRequest,
    current: CurrentUser,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.MANAGER)),
) -> RedirectResponse:
    if not settings.billing_enabled:
        raise HTTPException(status_code=503, detail="Billing is not enabled.")
    org = get_organization(db, current.org_id)
    if org is None:
        raise HTTPException(status_code=400, detail="No organization on this account.")
    user = db.get(User, current.sub)
    email = user.email if user else "billing@engineergpt.local"
    try:
        url = service.create_checkout_session(db, org, plan=body.plan, email=email)
    except service.BillingDisabled as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RedirectResponse(url=url)


@router.post("/portal", response_model=RedirectResponse)
def portal(
    current: CurrentUser,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.MANAGER)),
) -> RedirectResponse:
    if not settings.billing_enabled:
        raise HTTPException(status_code=503, detail="Billing is not enabled.")
    org = get_organization(db, current.org_id)
    if org is None:
        raise HTTPException(status_code=400, detail="No organization on this account.")
    user = db.get(User, current.sub)
    email = user.email if user else "billing@engineergpt.local"
    try:
        url = service.create_portal_session(db, org, email=email)
    except service.BillingDisabled as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RedirectResponse(url=url)


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def webhook(request: Request, db: Session = Depends(get_db)) -> None:
    """Stripe webhook receiver. Verifies the signature before applying changes."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = service.verify_and_parse_event(payload, signature)
    except service.BillingDisabled as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # invalid signature / malformed payload
        raise HTTPException(status_code=400, detail="Invalid webhook.") from exc
    service.apply_subscription_event(db, event)
