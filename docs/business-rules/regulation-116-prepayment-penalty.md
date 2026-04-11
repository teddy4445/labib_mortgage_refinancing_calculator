# Regulation 116 Prepayment Penalty — Backend Logic Reference

This document is a project-friendly markdown reference derived from the mortgage refinance source materials.
It is intended to guide implementation of the real Phase 2 prepayment penalty engine.

## Scope
This document covers:
- applicability of prepayment penalty
- required rate conversion
- NPV-style Regulation 116 logic
- remaining payment stream usage
- market-rate bucket selection
- age-based discount factor
- implementation caveats

---

## 1. Applicability Rules

### Penalty-applicable track families
The source materials indicate that prepayment penalty applies to:
- fixed non-linked tracks
- fixed linked tracks
- some adjustable-rate tracks depending on reset interval / timing context

### Non-applicable track family
- prime-linked / prime floating tracks have **no prepayment penalty**

### Implementation rule
For Phase 2:
- `prime_floating` => return penalty not applicable
- `fixed_non_linked` => applicable
- `fixed_linked` => applicable
- `adjustable_non_linked` / `adjustable_linked` => compute only if available metadata is sufficient; otherwise return structured unsupported/warning result

Do not pretend adjustables are always penalty-free.
Do not pretend adjustables are always equivalent to fixed without required metadata.

---

## 2. Rate Conversion Rule

Annual rates must be converted to monthly periodic rates using the compound conversion rule:

```text
monthly_rate = (1 + annual_rate_decimal)^(1/12) - 1
```

Where `annual_rate_decimal = annual_rate_percent / 100`.

### Important rule
Do **not** use simple annual/12 division.

This rate-conversion rule must be shared with the Phase 1 payment engine so the codebase does not drift into inconsistent math.

---

## 3. Required Penalty Method

The intended method is an NPV-style present-value comparison.

### Core idea
The bank’s economic loss is based on comparing the present value of the remaining future payment stream under two discounting assumptions:

- `PV_market = PV(A)` using current relevant market rate `A`
- `PV_contract = PV(R)` using contract/original rate `R`

The penalty is based on the economic loss implied by this comparison, then reduced by the statutory age-based discount factor.

### Practical implementation rule
Implement the penalty engine around these steps:

1. determine whether the track is penalty-applicable
2. obtain the remaining future payments for the track
3. select the correct market annual rate for the remaining-duration bucket
4. convert both annual rates to monthly periodic rates
5. compute present value under market rate
6. compute present value under contract rate
7. derive economic loss
8. if there is no economic loss to compensate, return zero
9. apply the statutory discount factor by years since origination
10. round final user-facing penalty to the nearest shekel

---

## 4. Remaining Payment Stream

The penalty engine should use the **remaining future payments** of the track, not an oversimplified balance-only shortcut.

### Preferred implementation
Reuse amortization/payment helpers from Phase 1 if present.

The engine should either:
- build the remaining payment stream from track data, or
- receive a pre-built remaining payment stream from an upstream service/helper

### Minimum stream elements
A remaining payment stream should support:
- payment index / month number
- payment amount
- optionally remaining balance metadata if useful for debugging

---

## 5. Market Rate Bucket Selection

The current relevant market rate must be selected based on **remaining duration**, not original duration.

### Typical buckets
Support bucket logic equivalent to:
- up to 5 years
- 5–10 years
- 10–15 years
- 15–20 years
- 20–25 years
- 25–30 years

### Implementation rule
Input should support injected market-rate lookups, for example:
- normalized snapshots from the future Phase 4 market-data layer
- service-provided bucket rates
- deterministic test fixtures

Do not hardcode remote fetch logic into the penalty formula implementation.

---

## 6. Statutory Age-Based Discount Factor

After economic loss is determined, apply the regulatory discount factor based on years since origination:

- `< 3 years` => factor `1.00`
- `>= 3 and < 5 years` => factor `0.80`
- `>= 5 years` => factor `0.70`

### Implementation rule
This factor should be its own helper function.

Suggested function behavior:
- input: `years_since_origination`
- output: `1.0`, `0.8`, or `0.7`
- validate negative values as invalid

---

## 7. Sign Convention / Economic-Loss Handling

One of the narrative examples in the source material appears to have an inconsistency in how the intermediate sign is explained.
That should not block implementation.

### Safe implementation rule
The backend should encode the **economic outcome** rather than relying blindly on narrative sign wording:

- if the bank has no compensable economic loss, penalty should be `0`
- if the bank does have a compensable economic loss, apply the discount factor and return the resulting penalty

### Engineering recommendation
In code and tests, make this explicit.
For example:
- compute both PV values
- derive an `economic_loss_nis` value that is explicitly floored at zero before discounting
- document the convention in code comments and docs

This avoids sign confusion leaking into production behavior.

---

## 8. Suggested Structured Output

The penalty engine should return rich structured results, for example:

```json
{
  "applicable": true,
  "reason_code": "REG116_FIXED_TRACK",
  "warning_codes": [],
  "remaining_months": 180,
  "market_rate_bucket": "10_TO_15_YEARS",
  "market_annual_rate_percent": 3.8,
  "contract_annual_rate_percent": 4.5,
  "market_monthly_rate": 0.003123,
  "contract_monthly_rate": 0.003679,
  "pv_market_nis": 855000,
  "pv_contract_nis": 863420,
  "economic_loss_nis": 8420,
  "discount_factor": 0.70,
  "penalty_after_discount_nis": 5894,
  "rounded_penalty_nis": 5894
}
```

Exact naming can match repo style, but the engine should expose equivalent detail.

---

## 9. Error and Warning Handling

Return structured errors/warnings for cases such as:
- unsupported track type
- missing contract rate
- missing remaining months
- missing market-rate bucket
- insufficient adjustable-track metadata
- invalid years since origination
- malformed remaining payment stream

Prefer explicit reason/warning codes over vague fallback behavior.

---

## 10. Required Tests

At minimum, test:

### applicability
- fixed tracks applicable
- prime tracks not applicable
- adjustable tracks structured correctly based on available metadata

### discount factor
- boundary values around 3 and 5 years

### bucket selection
- boundary values by remaining months

### zero-penalty case
- case with no compensable economic loss returns zero

### positive-penalty case
- deterministic sample payment stream + rates yields positive discounted penalty

### integration
- total refinance cost aggregation includes per-track penalties and total penalty correctly

