# Refinance Costs — Business Rules Reference

This document is a project-friendly markdown reference derived from the mortgage refinance source materials.
It is intended for backend implementation of refinance cost logic.

## Scope
This document covers:
- advisor fee
- bank fee
- optional appraisal handling
- cost separation rules

It does **not** define the mathematical details of Regulation 116 prepayment penalty beyond saying it is a separate component. That logic is covered in `regulation-116-prepayment-penalty.md`.

---

## 1. Advisor Fee

### Meaning
The advisor/broker fee is the professional service fee paid to the human mortgage advisor handling the refinance process.

### Key rules
- It is a **fixed professional fee**.
- It is **not** a percentage of the loan amount.
- Refinancing consultation is usually more complex than initial mortgage acquisition.
- For a general-user refinance calculator, the recommended default estimate is:
  - **7000 NIS**
- The user should be able to override this with an actual quote.

### Why percentage logic is wrong
The source materials explicitly reject the logic of using a percentage of the loan amount.
Reason:
- advisor work does not scale proportionally with loan size
- a 2M loan is not double the advisory work of a 1M loan in normal comparable cases
- market pricing is typically a fixed-fee service band rather than a balance-based formula

### Implementation rule
Backend engine rule:
- default advisor fee = `7000`
- if `user_advisor_fee_quote` exists and is valid, use it instead
- output should record source metadata:
  - `default_estimate`
  - `user_override`

### Separation rule
Advisor fee is separate from:
- bank fees
- prepayment penalty
- appraisal fee

---

## 2. Bank Fee

### Meaning
Bank fees are the operational, registration, administrative, and legal/documentation costs charged by the bank side of the refinance process.

### Key rules
- They are separate from advisor fee.
- They are separate from prepayment penalty.
- They are separate from appraisal fee.
- For a general-user refinance calculator, the recommended default estimate is:
  - **3500 NIS**
- The user should be able to override this with an actual bank quote.

### Implementation rule
Backend engine rule:
- default bank fee = `3500`
- if `user_bank_fee_quote` exists and is valid, use it instead
- output should record source metadata:
  - `default_estimate`
  - `user_override`

### Notes from the business source
Typical bundled bank-fee assumptions may include:
- administrative / processing fees
- mortgage registration
- coordination charges
- standard documentation/legal costs

But the backend should not decompose these into fake precise subcomponents unless the product later requires it.
Use the bundled default unless a user override exists.

---

## 3. Appraisal Fee

### Meaning
Appraisal is a separate optional refinance cost and should not be merged into advisor or bank fee.

### Key rules
- appraisal is optional / conditional
- appraisal should be modelled as a separate component
- if the app knows appraisal is required, it should be included explicitly
- if the app does not know, do not silently hide it inside another number

### Implementation rule
Recommended backend behavior:
- include an explicit appraisal fee component in the refinance cost breakdown
- support either:
  - `included = false` and amount 0
  - `included = true` and amount from explicit input/config
- keep the field separate in outputs

---

## 4. Cost Separation Rules

The refinance cost engine must treat these as separate components:

1. advisor fee
2. bank fee
3. appraisal fee
4. prepayment penalty

### Forbidden shortcuts
Do **not**:
- calculate advisor fee as a percent of loan amount
- merge bank fee into advisor fee
- merge appraisal into bank fee
- merge prepayment penalty into generic “fees” without a separate field

### Required output behavior
The backend should return a structured breakdown, for example:

```json
{
  "advisor_fee": {"amount_nis": 7000, "source": "default_estimate"},
  "bank_fee": {"amount_nis": 3500, "source": "default_estimate"},
  "appraisal_fee": {"included": false, "amount_nis": 0},
  "prepayment_penalty_total_nis": 0,
  "total_refinance_cost_nis": 10500
}
```

---

## 5. Recommended Phase 2 Backend Output Expectations

For each refinance analysis result, the backend should expose:

- per-component fee breakdown
- total refinance cost
- source metadata for default vs override values
- per-track penalty breakdown
- overall penalty total
- warnings if some penalty components could not be calculated precisely

This structure is needed so later phases can compute:
- break-even
- NPV
- scenario ranking
- explanation tokens

