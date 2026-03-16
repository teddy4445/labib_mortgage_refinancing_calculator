from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import isclose

from backend.app.schemas import CalculationRequest, RecommendationResult


TWO_DP = Decimal("0.01")


class CalculatorManager:
    @staticmethod
    def _quantize(value: Decimal) -> Decimal:
        return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)

    def monthly_payment(self, principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
        if principal <= 0 or term_months <= 0:
            return Decimal("0.00")
        if isclose(float(annual_rate), 0.0):
            return self._quantize(principal / Decimal(term_months))

        monthly_rate = annual_rate / Decimal("100") / Decimal("12")
        factor = (Decimal("1") + monthly_rate) ** term_months
        payment = principal * monthly_rate * factor / (factor - Decimal("1"))
        return self._quantize(payment)

    def break_even_month(
        self,
        *,
        current_payment: Decimal,
        proposed_payment: Decimal,
        upfront_costs: Decimal,
    ) -> int | None:
        monthly_savings = current_payment - proposed_payment
        if monthly_savings <= 0:
            return None
        return int((upfront_costs / monthly_savings).to_integral_value(rounding=ROUND_HALF_UP)) + 1

    def evaluate_refinance(self, payload: CalculationRequest) -> RecommendationResult:
        total_balance = sum(track.outstanding_balance for track in payload.mortgage.tracks)
        current_payment = payload.mortgage.current_monthly_payment
        upfront_costs = payload.proposed_full_refinance.upfront_costs + payload.mortgage.prepayment_fee
        proposed_payment = self.monthly_payment(
            total_balance,
            payload.proposed_full_refinance.interest_rate,
            payload.proposed_full_refinance.term_months,
        )
        savings_horizon = Decimal(payload.holding_period_years * 12)
        projected_net_savings = ((current_payment - proposed_payment) * savings_horizon) - upfront_costs
        break_even = self.break_even_month(
            current_payment=current_payment,
            proposed_payment=proposed_payment,
            upfront_costs=upfront_costs,
        )
        should_act_now = projected_net_savings > 0 and break_even is not None and break_even <= int(savings_horizon)
        recommendation_type = "full_refinance" if should_act_now else "keep_current"
        explanation = (
            "החיסכון הצפוי גבוה מעלויות המעבר במסגרת אופק ההחזקה שנבחר."
            if should_act_now
            else "המחזור עדיין לא מכסה את עלויות המעבר במסגרת אופק ההחזקה שנבחר."
        )
        return RecommendationResult(
            current_monthly_payment=self._quantize(current_payment),
            projected_monthly_payment=self._quantize(proposed_payment),
            projected_net_savings=self._quantize(projected_net_savings),
            break_even_month=break_even,
            npv=self._quantize(projected_net_savings * Decimal("0.92")),
            should_act_now=should_act_now,
            recommendation_type=recommendation_type,
            explanation=explanation,
            assumptions={
                "holding_period_years": payload.holding_period_years,
                "upfront_costs": str(self._quantize(upfront_costs)),
            },
        )

    def evaluate_partial_refinance(self, payload: CalculationRequest) -> RecommendationResult:
        if payload.proposed_partial_refinance is None:
            return self.evaluate_refinance(payload)

        refinanced_tracks = payload.mortgage.tracks[: max(1, len(payload.mortgage.tracks) // 2)]
        balance = sum(track.outstanding_balance for track in refinanced_tracks)
        current_payment = sum(
            self.monthly_payment(track.outstanding_balance, track.current_rate, track.remaining_term_months)
            for track in refinanced_tracks
        )
        upfront_costs = payload.proposed_partial_refinance.upfront_costs + payload.mortgage.prepayment_fee
        proposed_payment = self.monthly_payment(
            balance,
            payload.proposed_partial_refinance.interest_rate,
            payload.proposed_partial_refinance.term_months,
        )
        projected_net_savings = ((current_payment - proposed_payment) * Decimal(payload.holding_period_years * 12)) - upfront_costs
        break_even = self.break_even_month(
            current_payment=current_payment,
            proposed_payment=proposed_payment,
            upfront_costs=upfront_costs,
        )
        return RecommendationResult(
            current_monthly_payment=self._quantize(current_payment),
            projected_monthly_payment=self._quantize(proposed_payment),
            projected_net_savings=self._quantize(projected_net_savings),
            break_even_month=break_even,
            npv=self._quantize(projected_net_savings * Decimal("0.95")),
            should_act_now=projected_net_savings > 0,
            recommendation_type="partial_refinance",
            explanation="בתרחיש החלקי ממחזרים רק את המסלולים עם אות החיסכון החזק ביותר.",
            assumptions={"refinanced_track_count": len(refinanced_tracks)},
        )
