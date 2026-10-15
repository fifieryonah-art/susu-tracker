# Assumptions and decisions

- One group runs one cycle. Each member receives exactly one payout in joining order.
- Membership closes with the first accepted payment, including a partial payment.
  Rejected payments and unsuccessful closure attempts do not lock membership.
- Names are trimmed, nonempty, case-sensitive strings: `Ama` and `ama` are distinct.
- Payments target the current week only. Week numbers must be integers, not booleans.
- Weeks advance only after successful closure, regardless of calendar dates.
- Every member contributes every week, including after receiving their payout.
- An incomplete closure returns outstanding balances without changing group state.
- After the final payout, the week counter advances to the next number, but the
  report marks the cycle complete and shows no further debts or next recipient.
  Contributions, additions, and closure are then rejected.
- Money inputs are GHS; internal balances are integer pesewas. Reports use exact
  two-decimal GHS strings. Inputs permit at most 12 whole digits and two decimal
  places, including trailing zeros. Floats are rejected.
- Payouts are recorded bookkeeping events; no bank transfer is performed.
- Direct Python API objects keep state in memory. Reports return copies to
  protect stored state. The CLI persists accepted actions to a versioned JSON
  file and replays them through the group rules when loading.
- Saved files are validated before use. Writes use a temporary file and atomic
  replacement. Creation refuses to overwrite existing data. Rejected operations
  and blocked closures do not write to the file.
- Run one CLI command at a time: storage does not lock against concurrent
  writers. The default file is `susu.json` in the current working directory.

# Improvements with more time

- Add file locking for concurrent commands and backup/recovery tools.
- Add dated payment receipts and an audit trail for corrections.
- Support multiple independent groups and explicitly starting another cycle.
