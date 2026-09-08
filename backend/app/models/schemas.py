"""Pydantic contracts shared across API routers."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Sector(str, Enum):
    DAIRY = "dairy"
    RETAIL = "retail"
    TEXTILES = "textiles"
    FOOD_PROCESSING = "food_processing"
    AGRISERVICES = "agriservices"
    POULTRY = "poultry"
    HANDICRAFTS = "handicrafts"
    OTHER = "other"


class SchemeName(str, Enum):
    MICRO_FINANCE = "Micro Finance Scheme"
    TERM_LOAN = "Term Loan Scheme"
    NOT_ELIGIBLE = "Not Eligible"


class LocationInput(BaseModel):
    village: str
    block: str
    district: str
    state: str


class FeasibilityRequest(BaseModel):
    location: LocationInput
    sector: Sector
    margin_capital: float = Field(gt=0, description="Available margin money (10% contribution), in INR")


class MarketReach(BaseModel):
    estimated_population_5km: int
    estimated_population_10km: int
    target_customer_base: int
    primary_distribution_channels: list[str]


class SWOT(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]


class CompetitorMapping(BaseModel):
    estimated_competitors_in_block: int
    density_assessment: str  # e.g. "low" | "medium" | "high"
    notes: str


class PricingInsight(BaseModel):
    suggested_price_range: str
    predicted_local_market_value: str
    rationale: str


class FeasibilityReport(BaseModel):
    location: LocationInput
    sector: Sector
    market_reach: MarketReach
    opportunity_analysis: list[str]
    swot: SWOT
    threats: list[str]
    competitor_mapping: CompetitorMapping
    pricing: PricingInsight
    summary: str


# ---------- Finance ----------

class FinanceRequest(BaseModel):
    margin_capital: float = Field(gt=0, description="Available margin money in INR")
    monthly_operating_cost: Optional[float] = Field(default=None, ge=0)


class RepaymentRow(BaseModel):
    quarter: int
    opening_balance: float
    interest_due: float
    principal_repaid: float
    total_payment: float
    closing_balance: float
    phase: str  # "moratorium" | "repayment"


class LoanPlan(BaseModel):
    project_cost: float
    margin_money: float
    max_loan_amount: float
    scheme: SchemeName
    interest_rate_pa: float
    tenure_years: int
    moratorium_months: int
    quarterly_emi: float
    total_interest: float
    total_repayment: float
    working_capital_estimate: float
    schedule: list[RepaymentRow]
    advice: Optional[str] = None
