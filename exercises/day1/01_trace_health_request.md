# Exercise 01 — Trace a FastAPI Request

## Goal

Trace one ordinary HTTP request through the backend.

## Time

Approximately 20–25 minutes.

## Starting point

The application is running and exposes:

```text
GET /health
```

## Task

Use Postman and the project source to determine how the request moves through the application.

Record:

```text
HTTP method:
Path:
HTTP status:
Response body:

FastAPI application file:
Application router file:
Route file:
Response model:
Route handler function:
```

Then draw the request flow from Postman to the returned JSON.

## Questions to discuss

1. Which file decides that `/health` is a GET endpoint?
2. Which file connects the route to the FastAPI application?
3. Where is the shape of the response defined?
4. Does this endpoint need Claude? Why or why not?
5. What would have to change if this route needed to become `/api/health`?

## Deliverable

Be ready to explain the full request flow in approximately one minute.

Do not add Claude to this endpoint.
