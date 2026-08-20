# Exercise 02 — Ground `/generate-response` with Order Data

## Goal

Extend the Day 1 response-generation feature so Claude can use verified order
information retrieved by the application.

## Time

Approximately 25 minutes.

## Starting point

You already have:

```text
POST /generate-response
ResponseService
ClaudeService
OrderRepository
GenerateResponseRequest / GenerateResponseResponse
```

The Day 1 endpoint can draft a response but cannot know verified order state.

## Requirement

Evolve `/generate-response` so that it can accept a customer/order reference,
retrieve the matching order through application code, and supply retrieved
order context to response generation.

The API response should make it possible to tell whether trusted order context
was actually used.

## Constraints

- Do not query MongoDB from `ClaudeService`.
- Do not give Claude direct database access.
- Do not trust an `order_id` without scoping it to the customer.
- Keep MongoDB access inside a repository.
- Keep response drafting inside the response-generation service layer.
- Do not invent order status when the lookup returns no authorized record.

## Test cases

Test:

1. a valid customer + order pair
2. the same order under a different customer
3. an order ID supplied without a customer ID

Record:

```text
case:
HTTP status:
trusted order context used?
what did the generated response claim?
```

## Deliverable

Explain which facts came from MongoDB, which text came from Claude, and which
decisions remained application-controlled.
