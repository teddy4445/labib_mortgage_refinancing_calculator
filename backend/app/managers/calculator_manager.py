from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from backend.app.core.config import Settings
from backend.app.domain.costs import calculate_refinance_cost_breakdown
from backend.app.domain import calculate_monthly_payment, calculate_total_monthly_payment
from backend.app.domain.analysis import build_recommendation_outcome
from backend.app.domain.market_data.models import MortgageRateBucketRecord
from backend.app.domain.exceptions import DomainError, MissingMarketInputError
from backend.app.domain.models import MarketContext, MortgageTrack, TrackType
from backend.app.domain.scenarios import (
    CostComponent,
    PrimeRobustnessAnalysis,
    RefinanceCostBreakdown,
    ScenarioEvaluation,
    ScenarioType,
    build_full_refinance_portfolio,
    build_status_quo_scenario,
    derive_recommendation_tokens,
    derive_scenario_tokens_and_risks,
    evaluate_prime_robustness,
    evaluate_scenario_portfolio,
    generate_partial_track_subsets,
    rank_scenarios,
)
from backend.app.domain.scenarios.generator import build_replacement_track
from backend.app.schemas import (
    BreakEvenView,
    CalculationRequest,
    CurrentMortgageSummary,
    MarketInputs,
    MortgageInput,
    NpvView,
    PrimeRobustnessPathView,
    PrimeRobustnessView,
    RecommendationRankingItemView,
    RecommendationResult,
    RecommendationSummaryView,
    RefinanceCostBreakdownView,
    RefinanceCostComponentView,
    RefinanceOffer,
    ScenarioView,
    TrackPenaltyBreakdownView,
    TrackInput,
    TrackPaymentBreakdown,
)


TWO_DP = Decimal("0.01")
PHASE_3_ENGINE_VERSION = "phase3-scenarios-v1"


class CalculatorManager:
    def __init__(self, settings: Settings | None = None) -> None:
        self._default_advisor_fee = (
            settings.refinance_default_advisor_fee if settings is not None else Decimal("7000")
        )
        self._default_bank_fee = (
            settings.refinance_default_bank_fee if settings is not None else Decimal("3500")
        )
        self._default_appraisal_fee = (
            settings.refinance_default_appraisal_fee if settings is not None else Decimal("2500")
        )
        self._annual_discount_rate = (
            settings.analysis_default_annual_discount_rate if settings is not None else Decimal("4.0")
        )
        self._prime_modest_increase = (
            settings.analysis_prime_modest_annual_increase if settings is not None else Decimal("0.25")
        )
        self._partial_subset_limit = settings.analysis_partial_subset_limit if settings is not None else 64

    @staticmethod
    def _quantize(value: Decimal) -> Decimal:
        return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)

    def monthly_payment(self, principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
        return self._quantize(
            calculate_monthly_payment(
                principal_nis=principal,
                annual_rate_percent=annual_rate,
                remaining_months=term_months,
            )
        )

    def _to_market_context(self, market_inputs: MarketInputs | None) -> MarketContext:
        if market_inputs is None:
            return MarketContext()
        return MarketContext(
            boi_base_rate=market_inputs.boi_base_rate,
            current_cpi=market_inputs.current_cpi,
            as_of=market_inputs.as_of,
        )

    def _to_market_rate_records(self, market_inputs: MarketInputs | None) -> list[MortgageRateBucketRecord]:
        if market_inputs is None:
            return []
        return [
            MortgageRateBucketRecord(
                effective_date=item.effective_date,
                track_family=item.track_family,
                bucket_code=item.bucket_code,
                remaining_months_min=item.remaining_months_min,
                remaining_months_max=item.remaining_months_max,
                annual_rate_percent=item.annual_rate_percent,
                source_key=item.source_key or "request_payload",
            )
            for item in market_inputs.mortgage_rate_buckets
        ]

    def _to_domain_track(self, track: TrackInput) -> MortgageTrack:
        return MortgageTrack(
            track_id=track.track_id,
            label=track.label,
            track_type=TrackType.from_raw(track.track_type),
            outstanding_balance=track.outstanding_balance,
            current_rate=track.current_rate,
            original_rate=track.original_rate,
            remaining_term_months=track.remaining_term_months,
            linkage_type=track.linkage_type,
            rate_type=track.rate_type,
            reset_interval=track.reset_interval,
            next_reset_date=track.next_reset_date,
            amortization_method=track.amortization_method,
            prepayment_penalty_rule=track.prepayment_penalty_rule,
            original_cpi=track.original_cpi,
            bank_margin=track.bank_margin,
            years_since_origination=track.years_since_origination,
        )

    def _to_domain_tracks(self, tracks: list[TrackInput]) -> list[MortgageTrack]:
        return [self._to_domain_track(track) for track in tracks]

    def summarize_current_mortgage(
        self,
        mortgage: MortgageInput,
        market_inputs: MarketInputs | None = None,
    ) -> CurrentMortgageSummary:
        summary = calculate_total_monthly_payment(
            tracks=self._to_domain_tracks(mortgage.tracks),
            context=self._to_market_context(market_inputs),
        )
        return CurrentMortgageSummary(
            total_monthly_payment=self._quantize(summary.total_monthly_payment),
            total_outstanding_balance=self._quantize(summary.total_outstanding_balance),
            total_adjusted_balance=self._quantize(summary.total_adjusted_balance),
            track_breakdown=[
                TrackPaymentBreakdown(
                    label=result.label,
                    track_type=result.track_type.value,
                    monthly_payment=self._quantize(result.monthly_payment),
                    outstanding_balance=self._quantize(result.outstanding_balance),
                    adjusted_balance=self._quantize(result.adjusted_balance)
                    if result.adjusted_balance is not None
                    else None,
                    effective_annual_rate=result.effective_annual_rate,
                    monthly_rate=result.monthly_rate,
                    prepayment_penalty_applies=result.prepayment_penalty_applies,
                    linkage_type=result.linkage_type,
                    rate_type=result.rate_type,
                    reset_interval=result.reset_interval,
                    next_reset_date=result.next_reset_date,
                    metadata=result.metadata,
                )
                for result in summary.track_results
            ],
            assumptions={
                **summary.assumptions,
                "rounding_policy": "internal precision preserved; output monetary values rounded to 0.01 NIS",
            },
        )

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

    def _analysis_horizon_months(self, *, tracks: list[MortgageTrack], holding_period_years: int) -> int:
        max_track_term = max(track.remaining_term_months for track in tracks)
        return min(holding_period_years * 12, max_track_term)

    def _build_refinance_cost_breakdown(
        self,
        *,
        mortgage: MortgageInput,
        offer: RefinanceOffer,
        refinanced_tracks: list[MortgageTrack],
        market_context: MarketContext,
        market_rate_records: list[MortgageRateBucketRecord],
        allocation_ratio: Decimal = Decimal("1"),
    ) -> RefinanceCostBreakdown:
        costs = calculate_refinance_cost_breakdown(
            tracks=refinanced_tracks,
            market_context=market_context,
            market_rate_records=market_rate_records,
            years_since_origination=mortgage.years_since_origination,
            advisor_fee_override=mortgage.advisor_cost if mortgage.advisor_cost > 0 else None,
            bank_fee_override=mortgage.bank_cost if mortgage.bank_cost > 0 else None,
            appraisal_included=mortgage.appraisal_required or mortgage.appraisal_cost > 0,
            appraisal_amount=mortgage.appraisal_cost if mortgage.appraisal_cost > 0 else None,
            additional_costs=offer.upfront_costs,
            aggregated_prepayment_fee_override=mortgage.prepayment_fee if mortgage.prepayment_fee > 0 else None,
            default_advisor_fee=self._default_advisor_fee,
            default_bank_fee=self._default_bank_fee,
            default_appraisal_fee=self._default_appraisal_fee,
            allocation_ratio=allocation_ratio,
        )
        if allocation_ratio != Decimal("1"):
            warning_codes = sorted({*costs.warning_codes, "PARTIAL_COSTS_ALLOCATED_PRO_RATA"})
            metadata = {**costs.metadata, "allocation_method": "balance_pro_rata"}
            return RefinanceCostBreakdown(
                advisor_fee=costs.advisor_fee,
                bank_fee=costs.bank_fee,
                appraisal_fee=costs.appraisal_fee,
                legacy_other_costs=costs.legacy_other_costs,
                prepayment_penalty_total=costs.prepayment_penalty_total,
                track_penalties=costs.track_penalties,
                total_refinance_cost=costs.total_refinance_cost,
                source=costs.source,
                warning_codes=warning_codes,
                metadata=metadata,
            )
        return costs

    def _build_refinance_track(
        self,
        *,
        offer: RefinanceOffer,
        balance: Decimal,
        default_label: str,
    ) -> MortgageTrack:
        track_type = TrackType.from_raw(offer.track_type or TrackType.FIXED_NON_LINKED.value)
        default_linkage_type = offer.linkage_type
        if default_linkage_type is None:
            default_linkage_type = "cpi_linked" if track_type in {TrackType.FIXED_LINKED, TrackType.ADJUSTABLE_LINKED} else "non_linked"
        default_rate_type = offer.rate_type
        if default_rate_type is None:
            if track_type == TrackType.PRIME_FLOATING:
                default_rate_type = "prime"
            elif track_type in {TrackType.ADJUSTABLE_LINKED, TrackType.ADJUSTABLE_NON_LINKED}:
                default_rate_type = "adjustable"
            else:
                default_rate_type = "fixed"

        return build_replacement_track(
            balance=balance,
            offer_rate=offer.interest_rate,
            offer_term_months=offer.term_months,
            track_type=track_type,
            label=offer.label or default_label,
            bank_margin=offer.bank_margin,
            original_cpi=offer.original_cpi,
            linkage_type=default_linkage_type,
            rate_type=default_rate_type,
            reset_interval=offer.reset_interval,
            next_reset_date=offer.next_reset_date,
        )

    def _apply_scenario_annotations(
        self,
        *,
        scenario: ScenarioEvaluation,
        status_quo: ScenarioEvaluation,
        market_context: MarketContext,
        holding_horizon_months: int,
    ) -> ScenarioEvaluation:
        has_any_prime_exposure = any(track.track_type == TrackType.PRIME_FLOATING for track in scenario.portfolio_tracks) or any(
            track.track_type == TrackType.PRIME_FLOATING for track in status_quo.portfolio_tracks
        )
        if has_any_prime_exposure:
            try:
                scenario.robustness = evaluate_prime_robustness(
                    scenario=scenario,
                    status_quo=status_quo,
                    base_context=market_context,
                    annual_discount_rate_percent=self._annual_discount_rate,
                    holding_period_months=holding_horizon_months,
                    modest_annual_increase_percent=self._prime_modest_increase,
                )
            except MissingMarketInputError:
                scenario.robustness = PrimeRobustnessAnalysis(
                    has_prime_exposure=True,
                    beneficial_under_all_paths=False,
                    warning_codes=["MISSING_BOI_BASE_RATE"],
                )

        explanation_tokens, risk_flags = derive_scenario_tokens_and_risks(scenario=scenario, status_quo=status_quo)
        if scenario.robustness and "MISSING_BOI_BASE_RATE" in scenario.robustness.warning_codes:
            explanation_tokens = sorted({*explanation_tokens, "LOW_CONFIDENCE_INPUTS"})
            risk_flags = sorted({*risk_flags, "LOW_CONFIDENCE_INPUTS"})
        scenario.explanation_tokens = explanation_tokens
        scenario.risk_flags = risk_flags
        return scenario

    def _evaluate_full_scenario(
        self,
        *,
        payload: CalculationRequest,
        market_context: MarketContext,
        market_rate_records: list[MortgageRateBucketRecord],
        current_tracks: list[MortgageTrack],
        current_total_monthly_payment: Decimal,
        current_total_adjusted_balance: Decimal,
        horizon_months: int,
    ) -> ScenarioEvaluation:
        full_costs = self._build_refinance_cost_breakdown(
            mortgage=payload.mortgage,
            offer=payload.proposed_full_refinance,
            refinanced_tracks=current_tracks,
            market_context=market_context,
            market_rate_records=market_rate_records,
        )
        refinance_track = self._build_refinance_track(
            offer=payload.proposed_full_refinance,
            balance=current_total_adjusted_balance,
            default_label="Refinanced Mortgage",
        )
        return evaluate_scenario_portfolio(
            scenario_id="full_refinance",
            scenario_type=ScenarioType.FULL_REFINANCE,
            name_code="FULL_REFINANCE",
            description_code="REFINANCE_ALL_TRACKS",
            portfolio_tracks=build_full_refinance_portfolio(refinance_track),
            current_monthly_payment=current_total_monthly_payment,
            refinance_costs=full_costs,
            market_context=market_context,
            horizon_months=horizon_months,
            annual_discount_rate_percent=self._annual_discount_rate,
            refinanced_track_labels=[track.label for track in current_tracks],
            kept_track_labels=[],
            metadata={"replacement_track_type": refinance_track.track_type.value},
        )

    def _evaluate_partial_scenarios(
        self,
        *,
        payload: CalculationRequest,
        market_context: MarketContext,
        market_rate_records: list[MortgageRateBucketRecord],
        current_tracks: list[MortgageTrack],
        current_total_monthly_payment: Decimal,
        current_total_adjusted_balance: Decimal,
        horizon_months: int,
    ) -> list[ScenarioEvaluation]:
        if payload.proposed_partial_refinance is None:
            return []
        if len(current_tracks) < 2:
            return []

        subsets, subset_metadata = generate_partial_track_subsets(
            current_tracks,
            max_scenarios=self._partial_subset_limit,
        )
        scenarios: list[ScenarioEvaluation] = []

        for index, subset in enumerate(subsets, start=1):
            subset_tracks = list(subset)
            subset_summary = calculate_total_monthly_payment(tracks=subset_tracks, context=market_context)
            kept_tracks = [track for track in current_tracks if track.label not in {item.label for item in subset_tracks}]
            allocation_ratio = subset_summary.total_adjusted_balance / current_total_adjusted_balance
            cost_breakdown = self._build_refinance_cost_breakdown(
                mortgage=payload.mortgage,
                offer=payload.proposed_partial_refinance,
                refinanced_tracks=subset_tracks,
                market_context=market_context,
                market_rate_records=market_rate_records,
                allocation_ratio=allocation_ratio,
            )
            refinanced_track = self._build_refinance_track(
                offer=payload.proposed_partial_refinance,
                balance=subset_summary.total_adjusted_balance,
                default_label=f"Partial Refinance {index}",
            )
            scenario = evaluate_scenario_portfolio(
                scenario_id=f"partial_refinance_{index}",
                scenario_type=ScenarioType.PARTIAL_REFINANCE,
                name_code="PARTIAL_REFINANCE",
                description_code="REFINANCE_SELECTED_TRACKS",
                portfolio_tracks=[*kept_tracks, refinanced_track],
                current_monthly_payment=current_total_monthly_payment,
                refinance_costs=cost_breakdown,
                market_context=market_context,
                horizon_months=horizon_months,
                annual_discount_rate_percent=self._annual_discount_rate,
                refinanced_track_labels=[track.label for track in subset_tracks],
                kept_track_labels=[track.label for track in kept_tracks],
                metadata={
                    "subset_generation_strategy": subset_metadata["strategy"],
                    "subset_generated_count": subset_metadata["generated"],
                    "subset_total_possible": subset_metadata["total_possible"],
                    "replacement_track_type": refinanced_track.track_type.value,
                },
            )
            scenarios.append(scenario)

        return scenarios

    def _cost_component_view(self, component: CostComponent) -> RefinanceCostComponentView:
        return RefinanceCostComponentView(
            amount=self._quantize(component.amount),
            source=component.source,
            included=component.included,
            metadata=component.metadata,
        )

    def _cost_breakdown_view(self, costs: RefinanceCostBreakdown) -> RefinanceCostBreakdownView:
        return RefinanceCostBreakdownView(
            advisor_fee=self._cost_component_view(costs.advisor_fee),
            bank_fee=self._cost_component_view(costs.bank_fee),
            appraisal_fee=self._cost_component_view(costs.appraisal_fee),
            legacy_other_costs=self._cost_component_view(costs.legacy_other_costs),
            prepayment_penalty_total=self._quantize(costs.prepayment_penalty_total),
            track_penalties=[
                TrackPenaltyBreakdownView(
                    track_id=item.track_id,
                    track_label=item.track_label,
                    applicable=item.applicable,
                    reason_code=item.reason_code,
                    remaining_months=item.remaining_months,
                    market_rate_bucket=item.market_rate_bucket,
                    market_annual_rate_percent=item.market_annual_rate_percent,
                    contract_annual_rate_percent=item.contract_annual_rate_percent,
                    market_monthly_rate=item.market_monthly_rate,
                    contract_monthly_rate=item.contract_monthly_rate,
                    pv_market_nis=self._quantize(item.pv_market_nis) if item.pv_market_nis is not None else None,
                    pv_contract_nis=self._quantize(item.pv_contract_nis) if item.pv_contract_nis is not None else None,
                    economic_loss_nis=self._quantize(item.economic_loss_nis) if item.economic_loss_nis is not None else None,
                    discount_factor=item.discount_factor,
                    penalty_before_discount_nis=self._quantize(item.penalty_before_discount_nis),
                    penalty_after_discount_nis=self._quantize(item.penalty_after_discount_nis),
                    rounded_penalty_nis=self._quantize(item.rounded_penalty_nis),
                    warning_codes=item.warning_codes,
                    metadata=item.metadata,
                )
                for item in costs.track_penalties
            ],
            total_refinance_cost=self._quantize(costs.total_refinance_cost),
            source=costs.source,
            warning_codes=costs.warning_codes,
            metadata=costs.metadata,
        )

    def _break_even_view(self, scenario: ScenarioEvaluation) -> BreakEvenView:
        return BreakEvenView(
            break_even_months=scenario.break_even.break_even_months,
            break_even_years=self._quantize(scenario.break_even.break_even_years)
            if scenario.break_even.break_even_years is not None
            else None,
            raw_break_even_months=self._quantize(scenario.break_even.raw_break_even_months)
            if scenario.break_even.raw_break_even_months is not None
            else None,
            monthly_savings=self._quantize(scenario.break_even.monthly_savings),
            refinance_costs=self._quantize(scenario.break_even.refinance_costs),
            is_viable=scenario.break_even.is_viable,
            reason_code=scenario.break_even.reason_code,
        )

    def _npv_view(self, scenario: ScenarioEvaluation) -> NpvView:
        return NpvView(
            npv=self._quantize(scenario.npv.npv),
            total_present_value=self._quantize(scenario.npv.total_present_value),
            monthly_discount_rate=scenario.npv.monthly_discount_rate,
            annual_discount_rate=scenario.npv.annual_discount_rate,
            horizon_months=scenario.npv.horizon_months,
            is_positive=scenario.npv.is_positive,
            reason_code=scenario.npv.reason_code,
        )

    def _robustness_view(self, robustness: PrimeRobustnessAnalysis | None) -> PrimeRobustnessView | None:
        if robustness is None:
            return None
        return PrimeRobustnessView(
            has_prime_exposure=robustness.has_prime_exposure,
            beneficial_under_all_paths=robustness.beneficial_under_all_paths,
            path_results=[
                PrimeRobustnessPathView(
                    path_code=result.path_code,
                    boi_base_rate_start=result.boi_base_rate_start,
                    boi_base_rate_end=result.boi_base_rate_end,
                    projected_monthly_payment=self._quantize(result.projected_monthly_payment),
                    monthly_savings_vs_status_quo=self._quantize(result.monthly_savings_vs_status_quo),
                    npv=self._quantize(result.npv),
                    remains_beneficial=result.remains_beneficial,
                    warning_codes=result.warning_codes,
                )
                for result in robustness.path_results
            ],
            warning_codes=robustness.warning_codes,
        )

    def _scenario_view(self, scenario: ScenarioEvaluation) -> ScenarioView:
        return ScenarioView(
            id=scenario.id,
            scenario_type=scenario.type.value,
            name_code=scenario.name_code,
            description_code=scenario.description_code,
            refinanced_track_labels=scenario.refinanced_track_labels,
            kept_track_labels=scenario.kept_track_labels,
            current_monthly_payment=self._quantize(scenario.current_monthly_payment),
            proposed_monthly_payment=self._quantize(scenario.proposed_monthly_payment),
            monthly_savings=self._quantize(scenario.monthly_savings),
            total_outstanding_balance=self._quantize(scenario.total_outstanding_balance),
            total_adjusted_balance=self._quantize(scenario.total_adjusted_balance),
            refinance_costs=self._cost_breakdown_view(scenario.refinance_costs),
            break_even=self._break_even_view(scenario),
            npv=self._npv_view(scenario),
            risk_flags=scenario.risk_flags,
            explanation_tokens=scenario.explanation_tokens,
            robustness=self._robustness_view(scenario.robustness),
            recommendation_score=self._quantize(scenario.recommendation_score),
            metadata=scenario.metadata,
        )

    def _build_recommendation_result(
        self,
        *,
        current_summary: CurrentMortgageSummary,
        scenarios: list[ScenarioEvaluation],
        holding_period_years: int,
        analysis_kind: str,
        market_context: MarketContext,
    ) -> RecommendationResult:
        status_quo = next(scenario for scenario in scenarios if scenario.type == ScenarioType.STATUS_QUO)
        ranked_scenarios = rank_scenarios(scenarios)
        explanation_tokens = derive_recommendation_tokens(ranked_scenarios=ranked_scenarios, status_quo=status_quo)
        recommendation_summary = build_recommendation_outcome(
            ranked_scenarios=ranked_scenarios,
            status_quo_scenario=status_quo,
            explanation_tokens=explanation_tokens,
        )
        best_scenario = next(scenario for scenario in ranked_scenarios if scenario.id == recommendation_summary.best_scenario_id)
        horizon_months = best_scenario.npv.horizon_months
        projected_net_savings = (best_scenario.monthly_savings * Decimal(horizon_months)) - best_scenario.refinance_costs.total_refinance_cost
        status_quo_view = self._scenario_view(status_quo)
        best_scenario_view = self._scenario_view(best_scenario)
        ranked_views = [self._scenario_view(scenario) for scenario in ranked_scenarios]

        return RecommendationResult(
            current_monthly_payment=self._quantize(status_quo.current_monthly_payment),
            projected_monthly_payment=self._quantize(best_scenario.proposed_monthly_payment),
            projected_net_savings=self._quantize(projected_net_savings),
            break_even_month=best_scenario.break_even.break_even_months,
            npv=self._quantize(best_scenario.npv.npv),
            should_act_now=recommendation_summary.is_better_than_status_quo,
            recommendation_type=best_scenario.type.value,
            explanation=recommendation_summary.recommendation_code,
            assumptions={
                "holding_period_years": holding_period_years,
                "analysis_horizon_months": horizon_months,
                "analysis_discount_rate_annual": str(self._annual_discount_rate),
                "prime_modest_annual_increase": str(self._prime_modest_increase),
                "engine_version": PHASE_3_ENGINE_VERSION,
                "selected_scenario_id": best_scenario.id,
                "selected_total_refinance_cost": str(self._quantize(best_scenario.refinance_costs.total_refinance_cost)),
            },
            current_summary=current_summary,
            scenarios=ranked_views,
            recommendation_summary=RecommendationSummaryView(
                best_scenario_id=recommendation_summary.best_scenario_id,
                recommendation_code=recommendation_summary.recommendation_code,
                confidence=recommendation_summary.confidence,
                is_better_than_status_quo=recommendation_summary.is_better_than_status_quo,
                requires_human_followup_offer=recommendation_summary.requires_human_followup_offer,
                explanation_tokens=recommendation_summary.explanation_tokens,
                ranking=[
                    RecommendationRankingItemView(
                        scenario_id=item.scenario_id,
                        scenario_type=item.scenario_type,
                        rank=item.rank,
                        score=self._quantize(item.score),
                        is_better_than_status_quo=item.is_better_than_status_quo,
                        explanation_tokens=item.explanation_tokens,
                    )
                    for item in recommendation_summary.ranking
                ],
            ),
            explanation_tokens=recommendation_summary.explanation_tokens,
            risk_flags=best_scenario.risk_flags,
            analysis_kind=analysis_kind,
            calculated_at=datetime.now(timezone.utc),
            best_scenario=best_scenario_view,
            status_quo_scenario=status_quo_view,
            alternative_scenarios=[view for view in ranked_views if view.id != best_scenario_view.id],
            robustness_summary=self._robustness_view(best_scenario.robustness),
            found_better_alternative=recommendation_summary.is_better_than_status_quo,
            requires_human_followup_offer=recommendation_summary.requires_human_followup_offer,
            data_provenance={
                "market_inputs": {
                    "boi_base_rate": str(market_context.boi_base_rate) if market_context.boi_base_rate is not None else None,
                    "current_cpi": str(market_context.current_cpi) if market_context.current_cpi is not None else None,
                    "as_of": market_context.as_of.isoformat() if market_context.as_of is not None else None,
                },
                "analysis_engine_version": PHASE_3_ENGINE_VERSION,
                "cost_engine_source": best_scenario.refinance_costs.source,
            },
        )

    def evaluate_refinance(self, payload: CalculationRequest) -> RecommendationResult:
        market_context = self._to_market_context(payload.market_inputs)
        market_rate_records = self._to_market_rate_records(payload.market_inputs)
        current_tracks = self._to_domain_tracks(payload.mortgage.tracks)
        current_domain_summary = calculate_total_monthly_payment(tracks=current_tracks, context=market_context)
        current_summary = self.summarize_current_mortgage(payload.mortgage, payload.market_inputs)
        horizon_months = self._analysis_horizon_months(
            tracks=current_tracks,
            holding_period_years=payload.holding_period_years,
        )

        status_quo = build_status_quo_scenario(
            current_summary=current_domain_summary,
            current_tracks=current_tracks,
        )
        full_refinance = self._evaluate_full_scenario(
            payload=payload,
            market_context=market_context,
            market_rate_records=market_rate_records,
            current_tracks=current_tracks,
            current_total_monthly_payment=current_domain_summary.total_monthly_payment,
            current_total_adjusted_balance=current_domain_summary.total_adjusted_balance,
            horizon_months=horizon_months,
        )

        scenarios = [
            self._apply_scenario_annotations(
                scenario=status_quo,
                status_quo=status_quo,
                market_context=market_context,
                holding_horizon_months=horizon_months,
            ),
            self._apply_scenario_annotations(
                scenario=full_refinance,
                status_quo=status_quo,
                market_context=market_context,
                holding_horizon_months=horizon_months,
            ),
        ]
        return self._build_recommendation_result(
            current_summary=current_summary,
            scenarios=scenarios,
            holding_period_years=payload.holding_period_years,
            analysis_kind="full_refinance_analysis",
            market_context=market_context,
        )

    def evaluate_partial_refinance(self, payload: CalculationRequest) -> RecommendationResult:
        if payload.proposed_partial_refinance is None:
            return self.evaluate_refinance(payload)

        market_context = self._to_market_context(payload.market_inputs)
        market_rate_records = self._to_market_rate_records(payload.market_inputs)
        current_tracks = self._to_domain_tracks(payload.mortgage.tracks)
        current_domain_summary = calculate_total_monthly_payment(tracks=current_tracks, context=market_context)
        current_summary = self.summarize_current_mortgage(payload.mortgage, payload.market_inputs)
        horizon_months = self._analysis_horizon_months(
            tracks=current_tracks,
            holding_period_years=payload.holding_period_years,
        )

        status_quo = build_status_quo_scenario(
            current_summary=current_domain_summary,
            current_tracks=current_tracks,
        )
        full_refinance = self._evaluate_full_scenario(
            payload=payload,
            market_context=market_context,
            market_rate_records=market_rate_records,
            current_tracks=current_tracks,
            current_total_monthly_payment=current_domain_summary.total_monthly_payment,
            current_total_adjusted_balance=current_domain_summary.total_adjusted_balance,
            horizon_months=horizon_months,
        )
        partial_scenarios = self._evaluate_partial_scenarios(
            payload=payload,
            market_context=market_context,
            market_rate_records=market_rate_records,
            current_tracks=current_tracks,
            current_total_monthly_payment=current_domain_summary.total_monthly_payment,
            current_total_adjusted_balance=current_domain_summary.total_adjusted_balance,
            horizon_months=horizon_months,
        )

        all_scenarios = [status_quo, full_refinance, *partial_scenarios]
        annotated_scenarios = [
            self._apply_scenario_annotations(
                scenario=scenario,
                status_quo=status_quo,
                market_context=market_context,
                holding_horizon_months=horizon_months,
            )
            for scenario in all_scenarios
        ]
        return self._build_recommendation_result(
            current_summary=current_summary,
            scenarios=annotated_scenarios,
            holding_period_years=payload.holding_period_years,
            analysis_kind="partial_refinance_analysis",
            market_context=market_context,
        )
