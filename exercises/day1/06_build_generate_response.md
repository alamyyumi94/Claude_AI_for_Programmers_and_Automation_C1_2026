# Exercise 06 — Build a Customer Response Endpoint

## Goal

Build a second AI-powered backend use case while preserving the application's service boundaries.

## Time

Approximately 35–40 minutes.

## Requirement

Create:

```text
POST /generate-response
```

The endpoint receives a customer-support message and returns a draft response suitable for sending to the customer.

Return basic model/token usage with the draft.

## Important limitation

Day 1 has no trusted order or FAQ database integration yet.

The generated response must therefore avoid claiming private or business facts that the application has not supplied.

## Constraints

- Reuse `ClaudeService`.
- Keep the response-generation prompt outside the FastAPI route.
- Use an application service for the response-generation use case.
- Validate request and response data with Pydantic.
- Do not invent order status, refund status, account data, or company policy.
- Do not add MongoDB in this exercise.

## Test

Try at least two different support messages.

For each, ask:

> What facts did the backend genuinely know?

## Deliverable

A working Postman request and a short explanation of why the endpoint cannot yet give verified order-specific answers.

If you finish early, write down what trusted data you would want to retrieve on Day 2.
