"""Subscription plans and per-plan usage limits.

Plans are defined in code (not the database) so limits are versioned and
testable. An organization stores only its plan *key*; the concrete limits are
resolved here. ``-1`` means unlimited.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Plan(enum.StrEnum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


@dataclass(frozen=True)
class PlanLimits:
    key: Plan
    label: str
    price_usd_month: int
    # Monthly quotas (per organization). -1 == unlimited.
    monthly_analyses: int
    max_documents: int
    max_members: int
    features: tuple[str, ...]


PLANS: dict[Plan, PlanLimits] = {
    Plan.FREE: PlanLimits(
        key=Plan.FREE,
        label="Free",
        price_usd_month=0,
        monthly_analyses=50,
        max_documents=25,
        max_members=2,
        features=(
            "All 6 AI agents",
            "50 analyses / month",
            "25 stored documents",
            "Up to 2 teammates",
        ),
    ),
    Plan.PRO: PlanLimits(
        key=Plan.PRO,
        label="Pro",
        price_usd_month=29,
        monthly_analyses=2000,
        max_documents=1000,
        max_members=10,
        features=(
            "Everything in Free",
            "2,000 analyses / month",
            "1,000 stored documents",
            "Up to 10 teammates",
            "Priority processing",
        ),
    ),
    Plan.TEAM: PlanLimits(
        key=Plan.TEAM,
        label="Team",
        price_usd_month=99,
        monthly_analyses=-1,
        max_documents=-1,
        max_members=-1,
        features=(
            "Everything in Pro",
            "Unlimited analyses",
            "Unlimited documents",
            "Unlimited teammates",
            "Admin panel & audit",
        ),
    ),
}


def get_limits(plan: Plan | str) -> PlanLimits:
    """Resolve limits for a plan key, defaulting to Free for unknown values."""
    try:
        return PLANS[Plan(plan)]
    except ValueError:
        return PLANS[Plan.FREE]


def is_unlimited(value: int) -> bool:
    return value < 0
