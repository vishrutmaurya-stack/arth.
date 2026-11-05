"""Query guards: PII detection and intent classification before retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import Config

PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
AADHAAR_REGEX = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(
    r"(?:(?:\+91[\s-]?)|91[\s-]?)?[6-9]\d{9}\b"
    r"|\b(?:phone|mobile|call|contact|cell)\s*[:#-]?\s*\d{10}\b",
    re.IGNORECASE,
)
OTP_REGEX = re.compile(
    r"\b(?:otp|one[\s-]?time[\s-]?password)\b[\s:]*\d{4,8}\b"
    r"|\b\d{4,8}\b[\s:]*\b(?:otp|one[\s-]?time[\s-]?password)\b",
    re.IGNORECASE,
)
ACCOUNT_REGEX = re.compile(
    r"\b(?:a/c|account)\s*(?:no|num|number)?\s*[:#-]?\s*\d{6,18}\b",
    re.IGNORECASE,
)

ADVICE_PATTERNS = [
    re.compile(r"\b(?:should|shall)\s+i\s+(?:buy|sell|invest|choose|hold|switch)\b", re.IGNORECASE),
    re.compile(r"\b(?:recommend|recommendation|recommends|advis(?:e|e me|ing))\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+(?:of\s+these\s+)?(?:fund|scheme|one|these)?s?\s+is\s+better\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+is\s+better(?:\s+for\s+me)?\b", re.IGNORECASE),
    re.compile(r"\bbest\s+fund\s+for\s+me\b", re.IGNORECASE),
    re.compile(r"\b(?:portfolio\s+split|asset\s+allocation|allocate\s+my)\b", re.IGNORECASE),
    re.compile(r"\bsuggest\s+(?:a\s+)?(?:sip|fund|funds|investment|portfolio|amount)\b", re.IGNORECASE),
    re.compile(r"\bwhere\s+should\s+i\s+invest\b", re.IGNORECASE),
]

PERFORMANCE_PATTERNS = [
    re.compile(r"\bcagr\b", re.IGNORECASE),
    re.compile(r"\breturns?\b", re.IGNORECASE),
    re.compile(r"\bperformance\b", re.IGNORECASE),
    re.compile(r"\b(?:annualized|annualised|xirr|trailing\s+returns?)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*[\-]?\s*(?:year|yr|y)\s+(?:return|returns|cagr|growth|performance)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:return|returns|annualized|annualised|historical)\b.*\b(?:year|yr|3y|5y|1y|cagr)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:beat\s+the\s+benchmark|outperform(?:ed|ing)?)\b", re.IGNORECASE),
    re.compile(r"\b(?:best\s+performing|top\s+performing|highest\s+return)\b", re.IGNORECASE),
    re.compile(r"\b(?:compare\s+(?:the\s+)?performance|calculate\s+returns?)\b", re.IGNORECASE),
    re.compile(r"\b(?:which\s+fund\s+beat)\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    decision: str  # allow | refuse_pii | refuse_advice | refuse_performance
    message: str | None = None
    educational_link: str | None = None


def _get_educational_link(config: Config, intent: str) -> str:
    for link in config.educational_links:
        use_for = link.get("use_for") or []
        if intent in use_for and link.get("url"):
            return str(link.get("url"))
    return "https://investor.sebi.gov.in/"


def check_pii(query: str) -> bool:
    """Return True if the query contains PII-like data."""
    for pattern in (PAN_REGEX, AADHAAR_REGEX, EMAIL_REGEX, PHONE_REGEX, OTP_REGEX, ACCOUNT_REGEX):
        if pattern.search(query):
            return True
    return False


def evaluate_guards(query: str, config: Config) -> GuardResult:
    """Run safety guards before retrieval.

    1. PII: refuse immediately, never retrieve, do not persist the raw query.
    2. Intent: refuse buy/sell/recommend/which-is-better, and returns/CAGR/ranking.
    """
    cleaned = query.strip()

    if check_pii(cleaned):
        return GuardResult(
            allowed=False,
            decision="refuse_pii",
            message=(
                "Do not share PAN, Aadhaar, email, phone, OTP, or account details here. "
                "This assistant cannot look up statements or personal holdings."
            ),
        )

    for pat in ADVICE_PATTERNS:
        if pat.search(cleaned):
            return GuardResult(
                allowed=False,
                decision="refuse_advice",
                message=(
                    "I cannot give investment advice, buy or sell recommendations, or a portfolio split. "
                    "Mutual fund investments are subject to market risks; use SEBI and AMFI educational material "
                    "and a registered advisor if you need personal guidance."
                ),
                educational_link=_get_educational_link(config, "advice"),
            )

    for pat in PERFORMANCE_PATTERNS:
        if pat.search(cleaned):
            return GuardResult(
                allowed=False,
                decision="refuse_performance",
                message=(
                    "I cannot calculate, rank, or compare past performance, returns, or CAGR. "
                    "Past performance is not indicative of future results; check official AMFI or AMC factsheets "
                    "rather than asking this assistant to compute them."
                ),
                educational_link=_get_educational_link(config, "performance"),
            )

    return GuardResult(allowed=True, decision="allow")
