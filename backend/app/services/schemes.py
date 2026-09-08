"""
GramAI — Government Scheme Intelligence

Structured government-scheme registry with JSONLogic-style eligibility rules.

Important:
- Eligibility is advisory, not a guarantee of approval.
- Final eligibility, subsidy, interest rate and documentation must be
  verified with the relevant government/bank/implementing agency.
- Scheme limits are represented as prototype decision-support rules.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any


# ---------------------------------------------------------------------------
# Scheme documents / local RAG data
# ---------------------------------------------------------------------------

_DOCS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "scheme_docs.json",
)


@lru_cache(maxsize=1)
def load_scheme_docs() -> list[dict[str, Any]]:
    """Load locally stored scheme documents for retrieval."""
    try:
        with open(_DOCS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return data.get("documents", [])

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    return []


# ---------------------------------------------------------------------------
# Scheme registry
# ---------------------------------------------------------------------------

SCHEMES: list[dict[str, Any]] = [
    {
        "slug": "mudra",
        "name": "Pradhan Mantri MUDRA Yojana",
        "level": "central",

        "min_loan": 10_000,
        "max_loan": 2_000_000,

        "interest_guidance": (
            "Interest rate is determined by the lending institution. "
            "Collateral-free micro-enterprise financing."
        ),

        "documents_required": [
            "Aadhaar",
            "PAN",
            "Bank statement",
            "Business/project details",
        ],

        "description_md": (
            "PMMY provides institutional credit to micro enterprises. "
            "Categories include Shishu, Kishore, Tarun and Tarun Plus. "
            "Tarun Plus can cover loans above ₹10 lakh and up to ₹20 lakh "
            "for eligible borrowers who have successfully repaid a previous "
            "Tarun loan."
        ),

        "source_url": "https://www.mudra.org.in",

        "eligibility_rules": {
            "and": [
                {
                    ">=": [
                        {"var": "loan_amount"},
                        10_000,
                    ]
                },
                {
                    "<=": [
                        {"var": "loan_amount"},
                        2_000_000,
                    ]
                },
                {
                    "==": [
                        {"var": "sector_non_farm"},
                        True,
                    ]
                },
            ]
        },
    },

    {
        "slug": "pmegp",
        "name": "Prime Minister's Employment Generation Programme",
        "level": "central",

        "min_loan": 50_000,
        "max_loan": 5_000_000,

        "interest_guidance": (
            "Normal bank interest rate; margin-money subsidy is available "
            "subject to PMEGP rules and category/location."
        ),

        "documents_required": [
            "Aadhaar",
            "Project report",
            "PAN",
            "Category certificate, if applicable",
            "EDP training certificate, where applicable",
        ],

        "description_md": (
            "PMEGP is a credit-linked subsidy programme for eligible "
            "new micro-enterprises. Maximum admissible project cost is "
            "₹50 lakh for manufacturing and ₹20 lakh for service/business "
            "activities."
        ),

        "source_url": (
            "https://www.kviconline.gov.in/pmegpeportal/"
        ),

        "eligibility_rules": {
            "and": [
                {
                    ">=": [
                        {"var": "project_cost"},
                        100_000,
                    ]
                },
                {
                    "or": [
                        {
                            "and": [
                                {
                                    "==": [
                                        {"var": "sector_type"},
                                        "manufacturing",
                                    ]
                                },
                                {
                                    "<=": [
                                        {"var": "project_cost"},
                                        5_000_000,
                                    ]
                                },
                            ]
                        },
                        {
                            "and": [
                                {
                                    "==": [
                                        {"var": "sector_type"},
                                        "service",
                                    ]
                                },
                                {
                                    "<=": [
                                        {"var": "project_cost"},
                                        2_000_000,
                                    ]
                                },
                            ]
                        },
                        {
                            "and": [
                                {
                                    "==": [
                                        {"var": "sector_type"},
                                        "business",
                                    ]
                                },
                                {
                                    "<=": [
                                        {"var": "project_cost"},
                                        2_000_000,
                                    ]
                                },
                            ]
                        },
                    ]
                },
            ]
        },
    },

    {
        "slug": "stand_up_india",
        "name": "Stand-Up India",
        "level": "central",

        "min_loan": 1_000_000,
        "max_loan": 10_000_000,

        "interest_guidance": (
            "Interest and lending terms are determined under the applicable "
            "bank lending framework."
        ),

        "documents_required": [
            "Aadhaar",
            "PAN",
            "Detailed project report",
            "Caste certificate, if applicable",
            "Business documents",
        ],

        "description_md": (
            "Historically provided bank loans of ₹10 lakh to ₹1 crore "
            "for eligible SC/ST and women entrepreneurs establishing "
            "greenfield enterprises. Current availability must be verified "
            "before presenting it as an active financing option."
        ),

        "source_url": "https://www.standupmitra.in",

        "status": "verify_current_status",

        "eligibility_rules": {
            "and": [
                {
                    ">=": [
                        {"var": "loan_amount"},
                        1_000_000,
                    ]
                },
                {
                    "<=": [
                        {"var": "loan_amount"},
                        10_000_000,
                    ]
                },
                {
                    "or": [
                        {
                            "==": [
                                {"var": "is_scst"},
                                True,
                            ]
                        },
                        {
                            "==": [
                                {"var": "is_woman"},
                                True,
                            ]
                        },
                    ]
                },
            ]
        },
    },

    {
        "slug": "mahila_samriddhi",
        "name": "Mahila Samriddhi Yojana",
        "level": "central",

        "min_loan": 10_000,
        "max_loan": 125_000,

        "interest_guidance": (
            "Beneficiary interest rate can be 4% p.a. under applicable "
            "NSFDC framework."
        ),

        "documents_required": [
            "Aadhaar",
            "Backward class certificate",
            "Income certificate",
            "Skill/training proof, where applicable",
        ],

        "description_md": (
            "Concessional financing support for eligible women beneficiaries "
            "from backward classes through the applicable channelising "
            "agency framework."
        ),

        "source_url": "https://nsfdc.nic.in",

        "eligibility_rules": {
            "and": [
                {
                    "==": [
                        {"var": "is_woman"},
                        True,
                    ]
                },
                {
                    "<=": [
                        {"var": "project_cost"},
                        140_000,
                    ]
                },
            ]
        },
    },

    {
        "slug": "micro_finance_sca",
        "name": "Micro Finance Scheme (SCA)",
        "level": "state",

        "min_loan": 10_000,
        "max_loan": 125_000,

        "interest_guidance": (
            "Beneficiary interest rate around 6.5% p.a. under applicable "
            "NSFDC scheme framework."
        ),

        "documents_required": [
            "Aadhaar",
            "Income certificate",
            "Project report",
            "Bank details",
        ],

        "description_md": (
            "Micro-finance support routed through State Channelising "
            "Agencies for eligible beneficiaries and small projects."
        ),

        "source_url": "https://nsfdc.nic.in",

        "eligibility_rules": {
            "<=": [
                {"var": "project_cost"},
                140_000,
            ]
        },
    },

    {
        "slug": "term_loan_sca",
        "name": "Term Loan Scheme (SCA)",
        "level": "state",

        "min_loan": 126_000,
        "max_loan": 4_500_000,

        "interest_guidance": (
            "Concessional financing terms depend on the applicable "
            "State Channelising Agency framework."
        ),

        "documents_required": [
            "Aadhaar",
            "Income certificate",
            "Detailed project report",
            "Bank details",
        ],

        "description_md": (
            "Term-loan support for eligible beneficiaries through "
            "State Channelising Agencies for larger projects."
        ),

        "source_url": "https://nsfdc.nic.in",

        "eligibility_rules": {
            "and": [
                {
                    ">=": [
                        {"var": "project_cost"},
                        140_000,
                    ]
                },
                {
                    "<=": [
                        {"var": "project_cost"},
                        5_000_000,
                    ]
                },
            ]
        },
    },
]


# ---------------------------------------------------------------------------
# JSONLogic-style rule engine
# ---------------------------------------------------------------------------

def _resolve(value: Any, facts: dict[str, Any]) -> Any:
    """Resolve literals and {var: ...} expressions."""
    if isinstance(value, dict) and "var" in value:
        return _get_var(facts, value["var"])

    return value


def _get_var(facts: dict[str, Any], path: str) -> Any:
    """Read a variable from the facts dictionary."""
    if not path:
        return None

    current: Any = facts

    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None

    return current


def _eval_rule(rule: Any, facts: dict[str, Any]) -> bool:
    """Evaluate a small JSONLogic-style rule set."""

    if not isinstance(rule, dict):
        return bool(rule)

    if len(rule) != 1:
        return False

    operator, operands = next(iter(rule.items()))

    if operator == "and":
        return all(_eval_rule(item, facts) for item in operands)

    if operator == "or":
        return any(_eval_rule(item, facts) for item in operands)

    if operator == "==":
        left, right = operands
        return _resolve(left, facts) == _resolve(right, facts)

    if operator == "!=":
        left, right = operands
        return _resolve(left, facts) != _resolve(right, facts)

    if operator == ">=":
        left, right = operands
        left = _resolve(left, facts)
        right = _resolve(right, facts)

        if left is None or right is None:
            return False

        return left >= right

    if operator == "<=":
        left, right = operands
        left = _resolve(left, facts)
        right = _resolve(right, facts)

        if left is None or right is None:
            return False

        return left <= right

    if operator == ">":
        left, right = operands
        left = _resolve(left, facts)
        right = _resolve(right, facts)

        if left is None or right is None:
            return False

        return left > right

    if operator == "<":
        left, right = operands
        left = _resolve(left, facts)
        right = _resolve(right, facts)

        if left is None or right is None:
            return False

        return left < right

    return False


# ---------------------------------------------------------------------------
# MUDRA tier logic
# ---------------------------------------------------------------------------

def mudra_tier(loan_amount: float) -> str:
    """
    Determine the MUDRA category for the ACTUAL requested loan amount.

    Shishu   : up to ₹50,000
    Kishore  : above ₹50,000 to ₹5 lakh
    Tarun    : above ₹5 lakh to ₹10 lakh
    Tarun Plus: above ₹10 lakh to ₹20 lakh, subject to additional eligibility
    """

    if loan_amount <= 50_000:
        return "Shishu"

    if loan_amount <= 500_000:
        return "Kishore"

    if loan_amount <= 1_000_000:
        return "Tarun"

    if loan_amount <= 2_000_000:
        return "Tarun Plus"

    return "Above MUDRA"


# ---------------------------------------------------------------------------
# Scheme eligibility
# ---------------------------------------------------------------------------

def check_eligibility(
    loan_amount: float,
    project_cost: float,
    *,
    is_woman: bool = False,
    is_scst: bool = False,
    sector_non_farm: bool = True,
    sector_type: str = "business",
    previous_tarun_repaid: bool = False,
) -> list[dict[str, Any]]:
    """
    Evaluate all registered schemes against the applicant facts.

    Returns ranked scheme matches.

    NOTE:
    An 'eligible' result here means the prototype rules were satisfied.
    It does NOT mean the applicant is guaranteed approval.
    """

    facts = {
        "loan_amount": float(loan_amount),
        "project_cost": float(project_cost),
        "is_woman": bool(is_woman),
        "is_scst": bool(is_scst),
        "sector_non_farm": bool(sector_non_farm),
        "sector_type": sector_type.lower().strip(),
        "previous_tarun_repaid": bool(previous_tarun_repaid),
    }

    results: list[dict[str, Any]] = []

    for scheme in SCHEMES:
        slug = scheme["slug"]

        # ---------------------------------------------------------------
        # Special PMMY Tarun Plus condition
        # ---------------------------------------------------------------

        if slug == "mudra":
            if loan_amount > 1_000_000:
                eligible = (
                    loan_amount <= 2_000_000
                    and previous_tarun_repaid
                    and sector_non_farm
                )
            else:
                eligible = _eval_rule(
                    scheme["eligibility_rules"],
                    facts,
                )

        else:
            eligible = _eval_rule(
                scheme["eligibility_rules"],
                facts,
            )

        reasons: list[str] = []

        if eligible:
            reasons.append(
                "Prototype eligibility conditions are satisfied."
            )
        else:
            if slug == "mudra" and loan_amount > 1_000_000:
                reasons.append(
                    "Tarun Plus requires successful repayment of a "
                    "previous Tarun loan."
                )
            else:
                reasons.append(
                    "One or more prototype eligibility conditions "
                    "are not satisfied."
                )

        tier = None

        if slug == "mudra":
            tier = mudra_tier(loan_amount)

        result = {
            "scheme": scheme["name"],
            "slug": slug,
            "level": scheme["level"],
            "eligible": eligible,
            "tier": tier,
            "min_loan": scheme["min_loan"],
            "max_loan": scheme["max_loan"],
            "interest_guidance": scheme["interest_guidance"],
            "description_md": scheme["description_md"],
            "documents_required": scheme["documents_required"],
            "source_url": scheme["source_url"],
            "reasons": reasons,
            "verification_required": True,
        }

        if scheme.get("status"):
            result["status"] = scheme["status"]

        results.append(result)

    # Eligible schemes first.
    # Then rank by practical proximity to the requested project/loan size.
    results.sort(
        key=lambda item: (
            not item["eligible"],
            abs(
                float(item["max_loan"])
                - float(loan_amount)
            ),
        )
    )

    return results


# ---------------------------------------------------------------------------
# Individual scheme lookup
# ---------------------------------------------------------------------------

def get_scheme(slug: str) -> dict[str, Any] | None:
    """Return a scheme by slug."""
    for scheme in SCHEMES:
        if scheme["slug"] == slug:
            return scheme

    return None


# ---------------------------------------------------------------------------
# Local RAG-lite retrieval
# ---------------------------------------------------------------------------

def search_scheme_docs(
    query: str,
    *,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Lightweight local retrieval over scheme documents.

    This is intentionally RAG-lite for the prototype:
    document retrieval is local and keyword based rather than vector DB based.
    """

    documents = load_scheme_docs()

    if not documents:
        return []

    query_terms = {
        term.lower()
        for term in query.split()
        if len(term.strip()) >= 2
    }

    if not query_terms:
        return documents[:top_k]

    scored: list[tuple[int, dict[str, Any]]] = []

    for document in documents:
        text = " ".join(
            str(value)
            for value in document.values()
            if value is not None
        ).lower()

        score = sum(
            1
            for term in query_terms
            if term in text
        )

        if score > 0:
            scored.append((score, document))

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        document
        for _, document in scored[:top_k]
    ]


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def rank_schemes(
    loan_amount: float,
    project_cost: float,
    *,
    is_woman: bool = False,
    is_scst: bool = False,
    sector_non_farm: bool = True,
    sector_type: str = "business",
    previous_tarun_repaid: bool = False,
) -> list[dict[str, Any]]:
    """
    Public helper used by the analysis pipeline.
    """

    return check_eligibility(
        loan_amount=loan_amount,
        project_cost=project_cost,
        is_woman=is_woman,
        is_scst=is_scst,
        sector_non_farm=sector_non_farm,
        sector_type=sector_type,
        previous_tarun_repaid=previous_tarun_repaid,
    )