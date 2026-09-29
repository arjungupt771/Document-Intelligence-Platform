# Failure-case dataset

Every time a production QA answer or extraction is wrong in a way worth
tracking, add a case file here in the same schema as `EvaluationCase`
(see evaluation/models.py). Include a `notes` field explaining what went
wrong and why. Run `evaluation/runner.py` against this directory in CI so
a fixed bug can never silently regress.