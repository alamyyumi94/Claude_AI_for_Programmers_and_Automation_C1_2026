# Exercise 03 — Prompt Experiment for Developers

## Goal

Improve the predictability and usefulness of a Claude-powered feature by changing application-controlled instructions.

## Time

Approximately 25–30 minutes.

## Starting point

`POST /summarise` works.

The current summarisation instruction is intentionally minimal.

## Task

Improve the summarisation instruction so that the result is more useful for a customer-support backend.

Decide what properties a good backend summary should have.

Run the same input before and after your change.

Then test at least two additional customer messages with different tone or complexity.

## Record

For each version, note:

```text
What instruction changed?
What changed in the output?
What stayed inconsistent?
Did the summary invent anything?
Did token usage change significantly?
```

## Constraints

- Keep the response as plain text for this exercise.
- Do not add a new database.
- Do not hard-code expected answers for individual customer messages.
- Treat the customer message as the content being processed, not as the application's configuration.

## Deliverable

Be ready to explain one change that made the output more suitable for programmatic use, and one limitation that prompting alone did not solve.
