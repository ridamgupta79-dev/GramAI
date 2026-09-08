from fastapi import APIRouter

from app.finance.engine import compute_loan_plan
from app.models.schemas import FinanceRequest, LoanPlan

router = APIRouter()


@router.post("/plan", response_model=LoanPlan)
def plan(req: FinanceRequest) -> LoanPlan:
    """Smart Scheme Calculator: margin capital -> project cost -> scheme -> EMI roadmap."""
    return compute_loan_plan(req.margin_capital, req.monthly_operating_cost)
