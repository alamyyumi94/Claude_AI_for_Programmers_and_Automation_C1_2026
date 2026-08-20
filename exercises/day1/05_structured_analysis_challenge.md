# Exercise 05 — Structured Analysis Challenge

## Goal

Test a structured AI endpoint and distinguish AI judgement from application contract.

## Time

Approximately 25 minutes.

## Starting point

The application exposes:

```text
POST /analyse
```

## Step 1 — Predict before running

Your group will receive a support message.

Before sending it, predict the likely:

```text
category
sentiment
priority
whether an order lookup may be required
whether policy/FAQ information may be required
whether human review may be required
```

Record your prediction.

## Step 2 — Run the request

Send the message to `/analyse`.

Record the structured result and token usage.

## Step 3 — Compare

Discuss:

1. Which parts matched your prediction?
2. Which parts differed?
3. Did the response keep the same schema as other groups?
4. Which values are constrained by the application?
5. Which values remain AI judgement?

## Step 4 — Validation check

Create one Python dictionary that is syntactically valid data but does **not** satisfy the application's analysis contract.

Use the application's Pydantic model to confirm that validation rejects it.

## Deliverable

Be prepared to show:

```text
prediction
actual result
one invalid object
validation result
```

Do not change the allowed enums just to make your invalid object pass.
