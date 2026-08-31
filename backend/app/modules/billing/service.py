"""Billing service — thin wrapper over the Stripe SDK.

Billing is optional. Every entry point raises :class:`BillingDisabled` when no
Stripe secret key is configured, so the platform runs free-only without Stripe.
The Stripe SDK is imported lazily so the dependency is only needed in production
billing deployments.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.plans import Plan
from app.models.organization import Organization


class BillingDisabled(RuntimeError):
    """Raised when a billing operation is attempted without Stripe configured."""


def _stripe() -> Any:
    if not settings.billing_enabled:
        raise BillingDisabled("Stripe billing is not configured on this instance.")
    import stripe  # lazy: only required when billing is actually used

    stripe.api_key = settings.stripe_secret_key
    return stripe


def price_for_plan(plan: Plan) -> str:
    mapping = {
        Plan.PRO: settings.stripe_price_pro,
        Plan.TEAM: settings.stripe_price_team,
    }
    price = mapping.get(plan, "")
    if not price:
        raise BillingDisabled(f"No Stripe price configured for plan '{plan.value}'.")
    return price


def plan_for_price(price_id: str) -> Plan | None:
    if price_id and price_id == settings.stripe_price_pro:
        return Plan.PRO
    if price_id and price_id == settings.stripe_price_team:
        return Plan.TEAM
    return None


def ensure_customer(db: Session, org: Organization, *, email: str) -> str:
    """Return the org's Stripe customer id, creating one on first use."""
    if org.stripe_customer_id:
        return org.stripe_customer_id
    customer = _stripe().Customer.create(
        email=email,
        name=org.name,
        metadata={"org_id": org.id, "org_slug": org.slug},
    )
    org.stripe_customer_id = customer["id"]
    db.add(org)
    db.commit()
    db.refresh(org)
    return str(customer["id"])


def create_checkout_session(
    db: Session, org: Organization, *, plan: Plan, email: str
) -> str:
    """Create a Stripe Checkout session and return its hosted URL."""
    stripe = _stripe()
    customer_id = ensure_customer(db, org, email=email)
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_for_plan(plan), "quantity": 1}],
        success_url=f"{settings.frontend_url}/billing?status=success",
        cancel_url=f"{settings.frontend_url}/billing?status=cancelled",
        metadata={"org_id": org.id, "plan": plan.value},
        allow_promotion_codes=True,
    )
    return str(session["url"])


def create_portal_session(db: Session, org: Organization, *, email: str) -> str:
    """Create a Stripe Billing Portal session so users can manage their plan."""
    stripe = _stripe()
    customer_id = ensure_customer(db, org, email=email)
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.frontend_url}/billing",
    )
    return str(session["url"])


def verify_and_parse_event(payload: bytes, signature: str) -> dict[str, Any]:
    stripe = _stripe()
    if not settings.stripe_webhook_secret:
        raise BillingDisabled("Stripe webhook secret is not configured.")
    event = stripe.Webhook.construct_event(
        payload=payload,
        sig_header=signature,
        secret=settings.stripe_webhook_secret,
    )
    return dict(event)


def apply_subscription_event(db: Session, event: dict[str, Any]) -> None:
    """Update org plan/subscription state from a Stripe webhook event."""
    etype = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    org = _resolve_org(db, obj)
    if org is None:
        return

    if etype in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "checkout.session.completed",
    }:
        _activate(db, org, obj)
    elif etype == "customer.subscription.deleted":
        _downgrade(db, org)


def _resolve_org(db: Session, obj: dict[str, Any]) -> Organization | None:
    org_id = (obj.get("metadata") or {}).get("org_id")
    if org_id:
        found = db.get(Organization, org_id)
        if found is not None:
            return found
    customer_id = obj.get("customer")
    if customer_id:
        from sqlalchemy import select

        return db.execute(
            select(Organization).where(
                Organization.stripe_customer_id == customer_id
            )
        ).scalar_one_or_none()
    return None


def _activate(db: Session, org: Organization, obj: dict[str, Any]) -> None:
    plan = plan_for_price(_extract_price_id(obj)) or Plan.PRO
    org.plan = plan.value
    org.subscription_status = obj.get("status") or "active"
    sub_id = obj.get("subscription") or obj.get("id")
    if isinstance(sub_id, str):
        org.stripe_subscription_id = sub_id
    db.add(org)
    db.commit()


def _downgrade(db: Session, org: Organization) -> None:
    org.plan = Plan.FREE.value
    org.subscription_status = "canceled"
    db.add(org)
    db.commit()


def _extract_price_id(obj: dict[str, Any]) -> str:
    items = (obj.get("items") or {}).get("data") or []
    if items:
        price = items[0].get("price") or {}
        return str(price.get("id", ""))
    return ""
