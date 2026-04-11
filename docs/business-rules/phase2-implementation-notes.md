# Phase 2 Implementation Notes for Codex

This document explains how the real Phase 2 engine should be integrated into the repo.

## 1. Goal
Replace any legacy/fallback refinance-cost path with a real structured engine.

The repo should stop treating refinance costs as a loose bundle and instead compute:
- advisor fee
- bank fee
- appraisal fee
- per-track prepayment penalty
- total refinance cost

## 2. Integration approach

### Keep router code thin
Routers/controllers should not contain formulas.

They should call a service such as:
- `CalculatorManager.calculate_refinance_costs(...)`
- or equivalent service function

### Service responsibilities
The service layer should:
1. normalize inputs
2. classify each track for penalty applicability
3. compute per-track penalty where applicable
4. compute advisor/bank/appraisal costs
5. aggregate all results
6. return typed structured output

### Domain responsibilities
Pure domain code should:
- convert rates
- build payment streams
- select market buckets
- compute PVs
- apply discount factors
- return structured numeric outputs

## 3. Reuse from earlier phases
If Phase 1 already exists, reuse:
- annual-to-monthly conversion helper
- amortization/payment helper
- canonical track models/types

Do not create duplicate math helpers with slightly different behavior.

## 4. Minimum data expected from caller
A penalty-applicable track calculation generally needs:
- track type
- outstanding balance or equivalent amortization inputs
- contract/original annual rate
- remaining months
- years since origination
- market annual rate for the correct bucket

For adjustable tracks, additional metadata may be required.
If it is missing, return a structured unsupported case rather than a fake number.

## 5. Temporary compatibility rule
If some legacy API paths still expect a single generic total, you may keep returning that total **in addition** to the new structured breakdown.
But the structured breakdown must become the real source of truth.

## 6. Warning strategy
Use explicit warning codes when precision is limited.
Examples:
- `ADJUSTABLE_TRACK_METADATA_INSUFFICIENT`
- `MARKET_RATE_LOOKUP_MISSING`
- `LEGACY_FALLBACK_USED`

The goal is to make any remaining approximation visible and isolated.

## 7. Suggested execution order for Codex
1. inspect current calculator/fallback logic
2. identify current cost output schema
3. add typed cost/penalty models
4. implement advisor/bank/appraisal engines
5. implement penalty applicability classifier
6. implement market bucket selector
7. implement Regulation 116 penalty calculator
8. integrate into service layer
9. update endpoint outputs
10. add tests
11. update docs

## 8. What good completion looks like
After implementation:
- fixed and prime tracks should no longer depend on legacy fallback cost logic
- refinance analysis responses should include structured component breakdowns
- later phases can use these outputs directly for break-even, NPV, and ranking
- any remaining unsupported cases should be explicit, not hidden

