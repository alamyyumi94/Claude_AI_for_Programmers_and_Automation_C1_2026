# Exercise 03 — FAQ Evidence Challenge

## Goal

Observe the difference between approved retrieved evidence and unsupported AI
knowledge.

## Time

Approximately 15 minutes.

## Starting point

The application exposes:

```text
POST /faq/ask
```

The database contains approved FAQ records.

Your instructor will assign your pair a question.

## Step 1 — Predict

Before sending the request, predict:

```text
Do you expect approved FAQ evidence?
Do you expect human review?
Do you expect a Claude call to be useful?
```

Do not inspect the complete FAQ dataset first.

## Step 2 — Run

Send the assigned question to:

```text
POST /faq/ask
```

Inspect:

```text
answer
sources
requires_human_review
usage
```

## Step 3 — Compare

Discuss:

1. What did MongoDB retrieve?
2. What did Claude contribute?
3. What did the application decide?
4. What happens when no approved evidence is found?
5. Why is general model knowledge not enough for an approved company-policy
   answer?

## Deliverable

Explain the flow:

```text
question -> retrieval -> evidence -> Claude -> application response
```
