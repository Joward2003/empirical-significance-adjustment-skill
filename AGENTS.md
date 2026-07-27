# Empirical Significance Adjustment Agent

Read `SKILL.md` first. This directory is a reusable Agent Skill for diagnosing and ethically adjusting statistically insignificant empirical results.

Operational rules:

1. Reproduce and preserve the baseline before changing anything.
2. Read `references/decision-rules.md` before recommending methods.
3. Use method IDs from `references/method-registry.json`.
4. Log every approved run, including insignificant and failed results; record p-value-selected or rejected attempts in `audit_events.jsonl`.
5. Verify the run with `scripts/verify_run_integrity.py` and generate the final report through `scripts/summarize_run.py`, using `assets/final-report-template.md`.
6. Do not select a model, sample, threshold, cluster, control set, or transformation solely because it yields a smaller p-value.
