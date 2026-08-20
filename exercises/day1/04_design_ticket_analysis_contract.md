# Exercise 04 — Design an AI Output Contract

## Goal

Design the data contract your backend should receive from Claude before seeing the course implementation.

## Time

Approximately 15 minutes.

## Scenario

SupportOps AI receives customer-support messages.

Later application logic must be able to decide things such as:

- what type of support issue this is
- how the customer feels
- how important the issue is
- whether another system needs to be consulted
- whether a human should review the case

## Task

Design the JSON object you would want Claude to return.

Your design should be specific enough that normal Python code could validate it and make decisions from it.

Think about:

- field names
- allowed values
- booleans vs free text
- optional fields
- relationships between fields

## Deliverable

One proposed JSON example and a short explanation of the rules you would validate.

Do not implement the Pydantic model yet unless the instructor asks you to.
