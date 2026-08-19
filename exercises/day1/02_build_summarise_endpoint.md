# Exercise 02 — Build the First Claude-Backed Endpoint

## Goal

Create a small FastAPI endpoint that calls Claude through the provided application service boundary.

## Time

Approximately 30 minutes.

## Requirement

Build:

```text
POST /summarise
```

The endpoint receives customer-support text and returns a concise summary.

The response must also expose basic Claude usage information so the caller can see which model was used and the input/output token counts.

## Constraints

- Use the existing `ClaudeService`.
- Do not put the Anthropic API key in source code.
- Do not create a new Anthropic client directly inside the route.
- Validate the input length.
- Return an explicit response model rather than the raw Anthropic SDK response.
- Keep the summary use case separate from the low-level Claude client.

## Test message

Use a realistic support complaint of at least a few sentences.

## Deliverable

A working request in Postman and a short explanation of:

```text
HTTP route
    ->
application code
    ->
ClaudeService
    ->
Claude
    ->
response model
```

After the endpoint works, test a substantially longer complaint and compare the input/output token counts with your first request.
