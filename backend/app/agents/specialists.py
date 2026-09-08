"""Specialist agents — one per dashboard topic."""
from __future__ import annotations

from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.finance.engine import compute_loan_plan
from app.services import llm_service, rag_service
from app.services.competitor_estimator import estimate_competitors


# =========================================================
# 1. Loan Eligibility
# =========================================================

class LoanEligibilityAgent(BaseAgent):
    topic = "loan_eligibility"
    retrieval_query = "margin money 10% loan 90% project cost eligibility"

    def compute(self, ctx: dict) -> dict:
        plan = compute_loan_plan(ctx["margin_capital"])

        return {
            "project_cost": plan.project_cost,
            "max_loan_amount": plan.max_loan_amount,
            "loan_to_value": "90%",
            "eligible": plan.scheme.value != "Not Eligible",
        }


# =========================================================
# 2. Scheme Recommendation
# =========================================================

class SchemeRecommendationAgent(BaseAgent):
    topic = "scheme_recommendation"
    retrieval_query = (
        "concessional loan scheme interest rate tenure "
        "moratorium women"
    )

    def compute(self, ctx: dict) -> dict:
        plan = compute_loan_plan(ctx["margin_capital"])

        recs = [
            {
                "scheme": plan.scheme.value,
                "interest_rate_pa": plan.interest_rate_pa,
                "tenure_years": plan.tenure_years,
                "moratorium_months": plan.moratorium_months,
                "reason": (
                    f"Project cost ₹{plan.project_cost:,.0f} "
                    "falls in this scheme's range."
                ),
            }
        ]

        # Cross-sell women-specific schemes
        if ctx.get("gender") == "female":
            from app.services.rag_service import retrieve

            for d in retrieve("women beneficiary concessional scheme"):
                if d["name"] not in [r["scheme"] for r in recs]:
                    recs.append(
                        {
                            "scheme": d["name"],
                            "note": "Women-focused scheme worth exploring.",
                        }
                    )

        return {"recommended": recs}


# =========================================================
# 3. Market Demand
# =========================================================

class MarketDemandAgent(BaseAgent):
    topic = "market_demand"
    retrieval_query = ""

    def compute(self, ctx: dict) -> dict:
        pop = ctx["demo"]["block_population"]

        pop5 = int(pop * 0.18)
        pop10 = int(pop * 0.35)
        base = int(pop10 * 0.4)

        return {
            "population_5km": pop5,
            "population_10km": pop10,
            "target_customer_base": base,
            "estimated_annual_demand_value": base * 1200,
            "distribution_channels": [
                "Weekly village haat / market",
                "Local kirana retailers",
                "Direct-to-consumer home delivery",
                "Block-level wholesale market",
            ],
        }


# =========================================================
# 4. Competitor Map
# =========================================================

class CompetitorMapAgent(BaseAgent):
    topic = "competitor_map"

    def compute(self, ctx: dict) -> dict:
        return estimate_competitors(
            ctx["demo"]["block_population"],
            ctx["sector"],
            ctx["demo"]["urbanization_factor"],
        )


# =========================================================
# 5. SWOT Analysis
# =========================================================

class SwotAgent(BaseAgent):
    topic = "swot_analysis"
    retrieval_query = ""

    def compute(self, ctx: dict) -> dict:
        sector = ctx["sector"].replace("_", " ")

        return {
            "strengths": [
                "Low operating overheads in rural location",
                "Concessional credit at subsidised interest rate",
                "Direct community relationships build trust quickly",
            ],
            "weaknesses": [
                "First-time entrepreneur without formal business training",
                "Limited working capital buffer beyond margin contribution",
                "Dependence on seasonal local demand",
            ],
            "opportunities": [
                f"Growing rural demand for quality {sector} services",
                "Tie-ups with SHGs and self-help collectives",
                "Digital payment adoption widens the customer base",
            ],
            "threats": [
                "Seasonal demand fluctuation tied to harvest cycles",
                "Supply chain bottlenecks for inputs",
                "Entry of better-funded competitors",
            ],
        }


# =========================================================
# 6. Risk Analysis
# =========================================================

class RiskAnalysisAgent(BaseAgent):
    topic = "risk_analysis"
    retrieval_query = "moratorium repayment default risk"

    def compute(self, ctx: dict) -> dict:
        plan = compute_loan_plan(ctx["margin_capital"])

        density = estimate_competitors(
            ctx["demo"]["block_population"],
            ctx["sector"],
            ctx["demo"]["urbanization_factor"],
        )["density_assessment"]

        risks = [
            {
                "risk": "Buyer concentration",
                "severity": "high" if density == "low" else "medium",
                "mitigation": (
                    "Sign up at least 3 regular buyers before launch."
                ),
            },
            {
                "risk": "Seasonal cash-flow dips",
                "severity": "medium",
                "mitigation": (
                    f"Keep {plan.moratorium_months}-month moratorium + "
                    "1 quarter of EMI as reserve."
                ),
            },
            {
                "risk": "Input price volatility",
                "severity": "medium",
                "mitigation": (
                    "Maintain two suppliers per critical input."
                ),
            },
            {
                "risk": "Repayment stress",
                "severity": (
                    "low"
                    if plan.quarterly_emi < plan.project_cost * 0.05
                    else "medium"
                ),
                "mitigation": (
                    f"Quarterly EMI is ₹{plan.quarterly_emi:,.0f}; "
                    "ensure this stays under 40% of quarterly profit."
                ),
            },
        ]

        return {
            "risks": risks,
            "overall_risk": "moderate",
        }


# =========================================================
# 7. Pricing
# =========================================================

class PricingAgent(BaseAgent):
    topic = "pricing_suggestions"
    retrieval_query = ""

    def compute(self, ctx: dict) -> dict:
        base = int(
            ctx["demo"]["block_population"] * 0.35 * 0.4
        )

        return {
            "strategy": (
                "Penetration pricing: 5–10% below nearest town rates "
                "for first 6 months"
            ),
            "predicted_local_market_value": base * 1200,
            "rationale": (
                "Based on rural per-capita consumption proxies; "
                "revisit after 2 quarters of sales data."
            ),
        }


# =========================================================
# 8. Working Capital
# =========================================================

class WorkingCapitalAgent(BaseAgent):
    topic = "working_capital"
    retrieval_query = "working capital loan margin"

    def compute(self, ctx: dict) -> dict:
        plan = compute_loan_plan(ctx["margin_capital"])

        monthly_opex = (
            ctx.get("monthly_operating_cost")
            or plan.project_cost * 0.02
        )

        return {
            "monthly_operating_cost_estimate": round(monthly_opex),
            "recommended_reserve_months": 6,
            "working_capital_requirement": round(monthly_opex * 6),
            "note": (
                "Fund via initial sales retention; "
                "MUDRA/SVANidhi top-ups possible later."
            ),
        }


# =========================================================
# 9. EMI Schedule
# =========================================================

class EmiScheduleAgent(BaseAgent):
    topic = "emi_schedule"
    retrieval_query = "repayment schedule moratorium quarterly instalment"

    def compute(self, ctx: dict) -> dict:
        plan = compute_loan_plan(ctx["margin_capital"])

        return {
            "scheme": plan.scheme.value,
            "quarterly_emi": plan.quarterly_emi,
            "total_interest": plan.total_interest,
            "total_repayment": plan.total_repayment,
            "schedule": [
                r.model_dump()
                for r in plan.schedule
            ],
        }


# =========================================================
# 10. Cash Flow
# =========================================================

class CashFlowAgent(BaseAgent):
    """12-quarter deterministic forecast with seasonal multipliers."""

    topic = "cash_flow_forecast"
    retrieval_query = ""

    SEASONALITY = [0.8, 0.9, 1.1, 1.2]

    def compute(self, ctx: dict) -> dict:
        plan = compute_loan_plan(ctx["margin_capital"])

        monthly_opex = (
            ctx.get("monthly_operating_cost")
            or plan.project_cost * 0.02
        )

        q_opex = monthly_opex * 3

        rows = []
        cum = -plan.margin_money

        for i, r in enumerate(plan.schedule):
            ramp = min(1.0, 0.5 + i * 0.08)
            season = self.SEASONALITY[i % 4]

            revenue = q_opex * 1.6 * ramp * season
            profit = revenue - q_opex
            net = profit - r.total_payment
            cum += net

            rows.append(
                {
                    "quarter": r.quarter,
                    "revenue": round(revenue),
                    "operating_cost": round(q_opex),
                    "gross_profit": round(profit),
                    "emi_payment": round(r.total_payment),
                    "net_cash_flow": round(net),
                    "cumulative_cash": round(cum),
                }
            )

        return {
            "forecast": rows,
            "break_even_quarter": next(
                (
                    r["quarter"]
                    for r in rows
                    if r["cumulative_cash"] > 0
                ),
                None,
            ),
        }


# =========================================================
# 11. AI Mentor
# =========================================================

class AiMentorAgent(BaseAgent):
    """
    Conversational mentor grounded in the user's analysis
    and retrieved scheme knowledge.

    The deterministic path is used first so the Advisor can
    answer reliably even without an LLM API key.
    """

    topic = "ai_mentor"
    retrieval_query = "government scheme guidance first time entrepreneur"

    def compute(self, ctx: dict) -> dict:
        return {
            "tips": [
                "Register on Udyam (free) to access priority-sector benefits.",
                "Open a current account separate from personal savings from day one.",
                "Record every sale — even on paper; banks ask for books at renewal.",
                "Use the moratorium period to build a customer base, not just set up shop.",
            ],
            "chat_available": True,
        }

    # ---------------------------------------------------------
    # Helper: recursively search nested report data
    # ---------------------------------------------------------

    @staticmethod
    def _find_value(data: Any, keys: set[str]) -> Any:
        """Search recursively for the first matching key."""

        if isinstance(data, dict):
            for key, value in data.items():
                if key in keys:
                    return value

            for value in data.values():
                found = AiMentorAgent._find_value(value, keys)
                if found is not None:
                    return found

        elif isinstance(data, list):
            for item in data:
                found = AiMentorAgent._find_value(item, keys)
                if found is not None:
                    return found

        return None

    # ---------------------------------------------------------
    # Helper: unwrap report sections
    # ---------------------------------------------------------

    @staticmethod
    def _prepare_analysis(dashboard_ctx: dict) -> dict:
        """
        Normalize both legacy and newer report structures.
        """

        raw = dashboard_ctx or {}

        if isinstance(raw, dict) and "sections" in raw:
            raw = raw["sections"]

        if not isinstance(raw, dict):
            return {}

        analysis: dict[str, Any] = {}

        for key, section in raw.items():

            if isinstance(section, dict) and "data" in section:
                data = section["data"]
            else:
                data = section

            analysis[key] = data

            # New analysis structure:
            # analysis -> data -> {
            #     market: {...},
            #     financials: {...},
            #     risk: {...},
            #     scheme_matches: [...]
            # }

            if key == "analysis" and isinstance(data, dict):
                analysis.update(data)

        return analysis

    # ---------------------------------------------------------
    # Helper: language
    # ---------------------------------------------------------

    @staticmethod
    def _is_hindi(language: str) -> bool:
        return str(language).strip().lower() == "hindi"

    # ---------------------------------------------------------
    # Helper: format scheme names
    # ---------------------------------------------------------

    @staticmethod
    def _scheme_names(scheme_data: Any) -> list[str]:
        names: list[str] = []

        if isinstance(scheme_data, list):
            items = scheme_data[:5]

        elif isinstance(scheme_data, dict):
            items = (
                scheme_data.get("recommended")
                or scheme_data.get("schemes")
                or []
            )

        else:
            items = []

        for item in items:
            if isinstance(item, dict):
                name = (
                    item.get("scheme")
                    or item.get("name")
                    or item.get("scheme_name")
                )

                if name:
                    names.append(str(name))

            elif isinstance(item, str):
                names.append(item)

        return names

    # ---------------------------------------------------------
    # Main Advisor
    # ---------------------------------------------------------

    def answer(
        self,
        question: str,
        dashboard_ctx: dict,
        language: str = "English",
    ) -> str:

        question = question.strip()
        question_lower = question.lower()

        hindi = self._is_hindi(language)

        # ---------------------------------------------------------
        # 1. Retrieve scheme information
        # ---------------------------------------------------------

        rag_ctx = rag_service.context_for_query(question)

        # ---------------------------------------------------------
        # 2. Normalize analysis/report structure
        # ---------------------------------------------------------

        analysis = self._prepare_analysis(dashboard_ctx)

        # ---------------------------------------------------------
        # 3. Pricing
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "price",
                "pricing",
                "charge",
                "rate",
                "कीमत",
                "दाम",
                "रेट",
                "प्राइस",
            ]
        ):

            pricing = self._find_value(
                analysis,
                {
                    "pricing_suggestions",
                    "pricing",
                },
            )

            if isinstance(pricing, dict):

                strategy = pricing.get("strategy")
                market_value = pricing.get(
                    "predicted_local_market_value"
                )

                if strategy:

                    if hindi:
                        answer = (
                            f"आपके बिज़नेस के लिए सुझाव है: {strategy}।"
                        )

                        if market_value is not None:
                            answer += (
                                f" इस विश्लेषण के अनुसार अनुमानित "
                                f"स्थानीय बाजार मूल्य ₹{market_value:,.0f} है।"
                            )

                        answer += (
                            " इसे शुरुआती अनुमान मानें और स्थानीय "
                            "प्रतिस्पर्धियों की कीमतों तथा ग्राहकों की "
                            "प्रतिक्रिया के आधार पर दोबारा जांचें।"
                        )

                    else:
                        answer = f"Recommended strategy: {strategy}."

                        if market_value is not None:
                            answer += (
                                f" The estimated local market value "
                                f"in this analysis is ₹{market_value:,.0f}."
                            )

                        answer += (
                            " Treat this as a starting estimate and "
                            "validate it against actual local competitor "
                            "prices and customer response."
                        )

                    return answer

            if hindi:
                return (
                    "सटीक कीमत बताने के लिए अभी पर्याप्त verified "
                    "transaction data उपलब्ध नहीं है। शुरुआत में "
                    "स्थानीय competitors की कीमत और आपकी operating cost "
                    "को देखकर price तय करें।"
                )

            return (
                "There is not enough verified transaction data to give "
                "a precise market price. Start with nearby competitor "
                "rates and your operating cost."
            )

        # ---------------------------------------------------------
        # 4. Competition
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "competitor",
                "competition",
                "nearby",
                "rival",
                "प्रतिस्पर्धी",
                "कंपटीटर",
                "competition",
            ]
        ):

            competitors = self._find_value(
                analysis,
                {
                    "competitor_map",
                    "market",
                    "competitors",
                },
            )

            if isinstance(competitors, dict):

                count = (
                    competitors.get("competitors_within_10km")
                    if competitors.get("competitors_within_10km")
                    is not None
                    else competitors.get(
                        "estimated_competitors_in_block"
                    )
                )

                if count is None:
                    count = competitors.get("count")

                if count is None:
                    count = competitors.get("competitor_count")

                density = (
                    competitors.get("competitor_density_per_km2")
                    if competitors.get("competitor_density_per_km2")
                    is not None
                    else competitors.get("density")
                )

                if count is not None:

                    if hindi:
                        answer = (
                            f"आपके वर्तमान analysis के अनुसार "
                            f"लगभग {count} nearby competitors हैं।"
                        )

                        if density is not None:
                            answer += (
                                f" अनुमानित competitor density "
                                f"{density} प्रति km² है।"
                            )

                        answer += (
                            " इसलिए launch से पहले उनकी pricing, "
                            "customer base और service quality compare करना "
                            "फायदेमंद रहेगा।"
                        )

                    else:
                        answer = (
                            f"The current analysis estimates "
                            f"{count} nearby competitors."
                        )

                        if density is not None:
                            answer += (
                                f" Estimated competitor density is "
                                f"{density} per km²."
                            )

                        answer += (
                            " Compare their pricing, customer base and "
                            "service quality before launching."
                        )

                    return answer

            count = self._find_value(
                analysis,
                {
                    "competitors_within_10km",
                    "estimated_competitors_in_block",
                    "competitor_count",
                },
            )

            if count is not None:
                if hindi:
                    return (
                        f"Analysis के अनुसार लगभग {count} nearby "
                        "competitors हैं।"
                    )

                return (
                    f"The analysis estimates {count} "
                    "nearby competitors."
                )

            if hindi:
                return (
                    "इस analysis में competitor count उपलब्ध नहीं है। "
                    "Market Map में nearby competition को verify करें।"
                )

            return (
                "The current analysis does not contain a competitor "
                "count. Check the Market Map to verify nearby competition."
            )

        # ---------------------------------------------------------
        # 5. Government schemes
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "scheme",
                "mudra",
                "pmegp",
                "subsidy",
                "government",
                "financial support",
                "योजना",
                "मुद्रा",
                "पीएमईजीपी",
                "सब्सिडी",
                "सरकारी",
            ]
        ):

            scheme_data = self._find_value(
                analysis,
                {
                    "scheme_matches",
                    "scheme_recommendation",
                    "schemes",
                    "recommended",
                },
            )

            names = self._scheme_names(scheme_data)

            if names:

                if hindi:
                    return (
                        "आपके वर्तमान business analysis के आधार पर "
                        "ये schemes match करती हैं: "
                        + ", ".join(names)
                        + "। आवेदन करने से पहले eligibility और latest "
                          "scheme terms को official government source "
                          "से verify करें।"
                    )

                return (
                    "Based on your current business analysis, "
                    "the matching schemes are: "
                    + ", ".join(names)
                    + ". Final eligibility and current scheme terms "
                      "should be verified with the latest official "
                      "government source before applying."
                )

            # Direct scheme dictionary
            if isinstance(scheme_data, dict):

                name = (
                    scheme_data.get("scheme")
                    or scheme_data.get("name")
                    or scheme_data.get("scheme_name")
                )

                if name:

                    if hindi:
                        return (
                            f"आपके current analysis के अनुसार "
                            f"{name} एक relevant scheme है। "
                            "Final eligibility और latest terms को "
                            "official government source से verify करें।"
                        )

                    return (
                        f"Based on the current analysis, {name} "
                        "is a relevant scheme match. Final eligibility "
                        "and current terms should be verified with the "
                        "latest official government source."
                    )

            # RAG-lite fallback
            if rag_ctx:

                if hindi:
                    return (
                        "उपलब्ध government-scheme references के आधार पर:\n\n"
                        f"{rag_ctx}\n\n"
                        "Eligibility और scheme terms को apply करने से "
                        "पहले latest official government source से verify करें।"
                    )

                return (
                    "Based on the available government-scheme references:\n\n"
                    f"{rag_ctx}\n\n"
                    "Eligibility and scheme terms should be verified "
                    "against the latest official government source "
                    "before applying."
                )

            if hindi:
                return (
                    "इस सवाल के लिए relevant scheme information अभी "
                    "retrieve नहीं हुई है। Final eligibility के लिए "
                    "official scheme authority से verification जरूरी है।"
                )

            return (
                "I can help compare government schemes, but the "
                "relevant scheme information was not retrieved. "
                "Final eligibility should be verified with the "
                "official scheme authority."
            )

        # ---------------------------------------------------------
        # 6. Risk
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "risk",
                "risky",
                "danger",
                "problem",
                "जोखिम",
                "रिस्क",
                "खतरा",
            ]
        ):

            risk = self._find_value(
                analysis,
                {
                    "risk_profile",
                    "risk_analysis",
                    "risk",
                },
            )

            if isinstance(risk, dict):

                overall = (
                    risk.get("overall")
                    or risk.get("overall_risk")
                    or risk.get("risk_level")
                    or risk.get("level")
                )

                factors = (
                    risk.get("risk_factors")
                    or risk.get("risks")
                    or risk.get("factors")
                    or []
                )

                high_risks = risk.get("high_risks")

                if overall:

                    if hindi:
                        answer = (
                            f"आपके business का overall assessed risk "
                            f"{overall} है।"
                        )

                        if high_risks is not None:
                            answer += (
                                f" Analysis में {high_risks} "
                                "high-risk factor(s) हैं।"
                            )

                    else:
                        answer = (
                            f"The overall assessed business risk "
                            f"is {overall}."
                        )

                        if high_risks is not None:
                            answer += (
                                f" The analysis identifies "
                                f"{high_risks} high-risk factor(s)."
                            )

                    readable_factors = []

                    if isinstance(factors, list):
                        for factor in factors[:3]:

                            if isinstance(factor, dict):

                                name = (
                                    factor.get("risk")
                                    or factor.get("factor")
                                    or factor.get("name")
                                )

                                severity = factor.get("severity")

                                if name:
                                    if severity:
                                        readable_factors.append(
                                            f"{name} ({severity})"
                                        )
                                    else:
                                        readable_factors.append(
                                            str(name)
                                        )

                            elif isinstance(factor, str):
                                readable_factors.append(factor)

                    if readable_factors:

                        if hindi:
                            answer += (
                                " मुख्य risk factors हैं: "
                                + ", ".join(readable_factors)
                                + "।"
                            )
                        else:
                            answer += (
                                " Key risk factors include: "
                                + ", ".join(readable_factors)
                                + "."
                            )

                    return answer

            overall = self._find_value(
                analysis,
                {
                    "overall",
                    "overall_risk",
                    "risk_level",
                },
            )

            if overall:

                if hindi:
                    return (
                        f"आपके business का overall assessed risk "
                        f"{overall} है।"
                    )

                return (
                    f"The overall assessed business risk "
                    f"is {overall}."
                )

            if hindi:
                return (
                    "इस report में complete risk assessment उपलब्ध नहीं है।"
                )

            return (
                "The current report does not contain a complete "
                "risk assessment."
            )

        # ---------------------------------------------------------
        # 7. Loan application questions
        # ---------------------------------------------------------

        application_words = [
            "apply",
            "application",
            "how to get loan",
            "how can i get loan",
            "how do i get loan",
            "loan process",
            "loan ke liye",
            "loan lena",
            "loan kaise",
            "आवेदन",
            "लोन के लिए",
            "लोन कैसे",
        ]

        if any(word in question_lower for word in application_words):

            if hindi:
                return (
                    "Loan के लिए सामान्य process यह रहेगा:\n"
                    "1. अपना business plan और project cost तैयार करें।\n"
                    "2. अपनी eligibility के अनुसार सही government scheme चुनें।\n"
                    "3. जरूरी documents जैसे identity proof, address proof, "
                    "business details और financial information तैयार रखें।\n"
                    "4. संबंधित bank या official scheme portal पर application करें।\n"
                    "5. Bank आपकी eligibility, documents और repayment capacity "
                    "verify करेगा।\n\n"
                    "GramAI आपके analysis के आधार पर suitable scheme और "
                    "estimated financing बता सकता है, लेकिन final approval "
                    "bank/scheme authority का होगा।"
                )

            return (
                "The usual loan application process is:\n"
                "1. Prepare your business plan and project cost.\n"
                "2. Select a government scheme that matches your eligibility.\n"
                "3. Keep identity proof, address proof, business details "
                "and financial information ready.\n"
                "4. Apply through the relevant bank or official scheme portal.\n"
                "5. The bank will verify eligibility, documents and repayment capacity.\n\n"
                "GramAI can identify suitable schemes and estimate financing "
                "from your analysis, but final approval belongs to the bank "
                "or scheme authority."
            )

        # ---------------------------------------------------------
        # 8. Loan / EMI
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "loan",
                "emi",
                "repayment",
                "borrow",
                "finance",
                "financing",
                "लोन",
                "ईएमआई",
                "कर्ज",
                "ऋण",
            ]
        ):

            loan = self._find_value(
                analysis,
                {
                    "emi_schedule",
                    "loan_eligibility",
                    "financials",
                    "financing",
                },
            )

            if isinstance(loan, dict):

                emi = (
                    loan.get("quarterly_emi")
                    if loan.get("quarterly_emi") is not None
                    else loan.get("emi")
                )

                if emi is None:
                    emi = loan.get("monthly_emi")

                if emi is None:
                    emi = loan.get("monthly_payment")

                total_interest = loan.get("total_interest")

                scheme = (
                    loan.get("scheme")
                    or loan.get("recommended_scheme")
                )

                loan_amount = (
                    loan.get("loan_amount")
                    or loan.get("max_loan_amount")
                )

                answer_parts = []

                if hindi:

                    if loan_amount is not None:
                        answer_parts.append(
                            f"आपके current analysis के अनुसार "
                            f"estimated loan amount ₹{loan_amount:,.0f} है।"
                        )

                    if emi is not None:
                        answer_parts.append(
                            f"Estimated repayment ₹{emi:,.0f} है।"
                        )

                    if scheme:
                        answer_parts.append(
                            f"Associated scheme {scheme} है।"
                        )

                    if total_interest is not None:
                        answer_parts.append(
                            f"Estimated total interest "
                            f"₹{total_interest:,.0f} है।"
                        )

                    if answer_parts:
                        return " ".join(answer_parts)

                else:

                    if loan_amount is not None:
                        answer_parts.append(
                            f"The estimated loan amount is "
                            f"₹{loan_amount:,.0f}."
                        )

                    if emi is not None:
                        answer_parts.append(
                            f"The current analysis estimates the "
                            f"repayment at ₹{emi:,.0f}."
                        )

                    if scheme:
                        answer_parts.append(
                            f"The associated scheme is {scheme}."
                        )

                    if total_interest is not None:
                        answer_parts.append(
                            "Estimated total interest is "
                            f"₹{total_interest:,.0f}."
                        )

                    if answer_parts:
                        return " ".join(answer_parts)

            if hindi:
                return (
                    "इस report में reliable loan/repayment calculation "
                    "के लिए पर्याप्त financial information उपलब्ध नहीं है।"
                )

            return (
                "The current report does not contain enough financial "
                "information to calculate a reliable repayment answer."
            )

        # ---------------------------------------------------------
        # 9. Market demand
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "demand",
                "customers",
                "customer",
                "market size",
                "market opportunity",
                "मांग",
                "ग्राहक",
                "मार्केट",
                "बाजार",
            ]
        ):

            market = self._find_value(
                analysis,
                {
                    "market",
                    "market_demand",
                },
            )

            if isinstance(market, dict):

                customers = market.get(
                    "target_customer_base"
                )

                population = (
                    market.get("population_within_10km")
                    if market.get("population_within_10km")
                    is not None
                    else market.get("population_10km")
                )

                opportunity = market.get(
                    "market_opportunity"
                )

                answer_parts = []

                if hindi:

                    if customers is not None:
                        answer_parts.append(
                            f"Estimated target customer base "
                            f"{customers:,} है।"
                        )

                    if population is not None:
                        answer_parts.append(
                            f"10 km के अंदर estimated reachable population "
                            f"{population:,} है।"
                        )

                    if opportunity:
                        answer_parts.append(
                            f"Market opportunity को {opportunity} assess किया गया है।"
                        )

                    if answer_parts:
                        return " ".join(answer_parts)

                else:

                    if customers is not None:
                        answer_parts.append(
                            f"The estimated target customer base "
                            f"is {customers:,}."
                        )

                    if population is not None:
                        answer_parts.append(
                            f"The estimated reachable population "
                            f"is {population:,}."
                        )

                    if opportunity:
                        answer_parts.append(
                            f"Market opportunity is assessed as "
                            f"{opportunity}."
                        )

                    if answer_parts:
                        return " ".join(answer_parts)

            customers = self._find_value(
                analysis,
                {
                    "target_customer_base",
                },
            )

            if customers is not None:

                if hindi:
                    return (
                        f"Analysis के अनुसार estimated target customer "
                        f"base {customers:,} है।"
                    )

                return (
                    f"The analysis estimates a target customer "
                    f"base of {customers:,}."
                )

            if hindi:
                return (
                    "इस report में market-demand information "
                    "answer करने के लिए पर्याप्त data उपलब्ध नहीं है।"
                )

            return (
                "The current report does not contain enough "
                "market-demand information to answer that."
            )

        # ---------------------------------------------------------
        # 10. Viability / business score
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "viability",
                "viable",
                "score",
                "business plan",
                "should i start",
                "worth starting",
                "व्यवहार्य",
                "स्कोर",
                "बिज़नेस शुरू",
                "business start",
            ]
        ):

            score = self._find_value(
                analysis,
                {
                    "viability_score",
                    "score",
                },
            )

            rating = self._find_value(
                analysis,
                {
                    "viability_rating",
                    "rating",
                },
            )

            if score is not None:

                if hindi:
                    answer = (
                        f"आपके current business viability score "
                        f"{score}/100 है।"
                    )

                    if rating:
                        answer += f" Rating: {rating}।"

                    answer += (
                        " Final decision लेने से पहले market demand, "
                        "competition, financing और repayment risk "
                        "को भी देखें।"
                    )

                else:
                    answer = (
                        f"The current business viability score "
                        f"is {score}/100."
                    )

                    if rating:
                        answer += f" The rating is {rating}."

                    answer += (
                        " Before making a final decision, also consider "
                        "market demand, competition, financing and "
                        "repayment risk."
                    )

                return answer

            if hindi:
                return (
                    "इस report में viability score उपलब्ध नहीं है।"
                )

            return (
                "The current report does not contain a viability score."
            )

        # ---------------------------------------------------------
        # 11. Working capital
        # ---------------------------------------------------------

        if any(
            word in question_lower
            for word in [
                "working capital",
                "cash needed",
                "operating cost",
                "working money",
                "वर्किंग कैपिटल",
                "working paisa",
            ]
        ):

            working = self._find_value(
                analysis,
                {
                    "working_capital",
                    "working_capital_requirement",
                },
            )

            if isinstance(working, dict):

                requirement = working.get(
                    "working_capital_requirement"
                )

                monthly_cost = working.get(
                    "monthly_operating_cost_estimate"
                )

                if requirement is not None:

                    if hindi:
                        answer = (
                            f"Recommended working-capital requirement "
                            f"लगभग ₹{requirement:,.0f} है।"
                        )

                        if monthly_cost is not None:
                            answer += (
                                f" Estimated monthly operating cost "
                                f"₹{monthly_cost:,.0f} है।"
                            )

                        return answer

                    answer = (
                        f"The recommended working-capital requirement "
                        f"is approximately ₹{requirement:,.0f}."
                    )

                    if monthly_cost is not None:
                        answer += (
                            f" Estimated monthly operating cost is "
                            f"₹{monthly_cost:,.0f}."
                        )

                    return answer

        # ---------------------------------------------------------
        # 12. LLM path
        # ---------------------------------------------------------

        if llm_service.llm_available():

            import json

            prompt = (
                "You are GramAI, a practical rural business advisor.\n\n"
                "Answer the user's question using ONLY the supplied "
                "business analysis context and retrieved scheme references.\n\n"
                "Do not invent numbers, eligibility rules, prices, "
                "subsidies, or government policies.\n"
                "If information is missing, clearly say that it is not available.\n"
                "Treat synthetic/demo market data as estimates, "
                "not verified real-world observations.\n"
                "For government schemes, recommend verification with "
                "the latest official source.\n"
                "Keep the answer concise, practical, and easy for "
                "a rural entrepreneur to understand.\n\n"
                f"Language: {language}\n\n"
                "Business analysis:\n"
                f"{json.dumps(analysis, ensure_ascii=False)[:8000]}\n\n"
                f"Retrieved scheme references:\n{rag_ctx}\n\n"
                f"User question:\n{question}"
            )

            out = llm_service.generate_json(
                prompt,
                'Respond only as {"answer": "..."}',
            )

            answer = out.get("answer")

            if answer:
                return answer

        # ---------------------------------------------------------
        # 13. Useful offline fallback
        # ---------------------------------------------------------

        if hindi:
            return (
                "मैं आपके business analysis के आधार पर सलाह दे सकता हूँ। "
                "आप मुझसे loan, EMI, government schemes, market demand, "
                "competitors, pricing, working capital, viability या risk "
                "के बारे में पूछ सकते हैं।"
            )

        return (
            "I can advise you using your business analysis. "
            "You can ask me about loans, EMI, government schemes, "
            "market demand, competitors, pricing, working capital, "
            "viability, or business risk."
        )

# =========================================================
# Run all specialist agents
# =========================================================

def run_all_agents(ctx: dict) -> dict[str, AgentResult]:
    agents = [
        LoanEligibilityAgent(),
        SchemeRecommendationAgent(),
        MarketDemandAgent(),
        CompetitorMapAgent(),
        SwotAgent(),
        RiskAnalysisAgent(),
        PricingAgent(),
        WorkingCapitalAgent(),
        EmiScheduleAgent(),
        CashFlowAgent(),
        AiMentorAgent(),
    ]

    return {
        a.topic: a.run(ctx)
        for a in agents
    }