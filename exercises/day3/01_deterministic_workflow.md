# Exercise 01 — Build the Deterministic Ticket Workflow

## Goal

Combine the application capabilities you already built into one deterministic multi-step workflow.

The sequence must be controlled by ordinary application code.

## Time

Approximately **45 minutes**.

## Starting point

The application already has working components for:

```text
ticket analysis
secure order retrieval
approved FAQ retrieval
ticket persistence
response generation
```

The workflow contract already exists:

```text
WorkflowStep
ProcessTicketRequest
ProcessTicketResponse
```

Your instructor will provide a `WorkflowService` starter whose `process()` method is not implemented.

## Important rule

This is a **deterministic workflow**.

> **Python/application code controls the sequence.**

Do not add tool calling or agent logic.

---

# Part 1 — Write pseudocode first

Before writing Python, agree on the workflow sequence.

Your pseudocode should answer:

```text
What happens first?

When is order lookup required?

When is FAQ lookup required?

What happens if required trusted context cannot be found?

When is the ticket created?

When is the response generated?

Who decides the final ticket status?

When is the ticket updated?
```

A possible shape is:

```text
analyse request

if order information is required:
    retrieve authorised order
    if order cannot be verified:
        require human review

if FAQ information is required:
    retrieve approved FAQ context
    if no approved FAQ is available:
        require human review

create ticket

generate response with trusted context

choose final status

update ticket

return result
```

Do not copy this mechanically. Check it against the services and repositories already present in your application.

---

# Part 2 — Implement `WorkflowService.process()`

Reuse existing components.

Do not:

```text
query MongoDB directly from WorkflowService
call the Anthropic SDK directly
create a second ClaudeService abstraction
duplicate TicketService logic
let Claude directly choose the final database status
```

Your workflow should record the steps that actually executed.

Possible `WorkflowStep` values include:

```text
ANALYSIS
ORDER_LOOKUP
FAQ_LOOKUP
DATABASE_INSERT
RESPONSE_GENERATION
DATABASE_UPDATE
```

Conditional steps should only appear when that branch runs.

---

# Part 3 — Business rules

Your workflow must preserve these ideas:

### Required order information

If analysis says order lookup is required:

```text
request has order_id
    -> perform customer-scoped lookup

no authorised order found
    -> require human review
```

Never invent missing order facts.

### Required FAQ information

If analysis says FAQ lookup is required:

```text
search approved FAQ data

no approved evidence
    -> require human review
```

### Final status

Claude may provide structured analysis, but the application owns the business result.

Consider:

```text
analysis already requests human review
urgent priority
missing required order context
missing required FAQ context
```

---

# Part 4 — Predict before testing

For each assigned scenario, write the expected steps **before** running it.

### Scenario A — delayed order

```text
customer_id: CUST-104
order_id: ORD-1005

My package was supposed to arrive yesterday. This is the third time I have had a delivery problem and I am really frustrated. Where is my order?
```

Prediction:

```text
Expected lookup(s):
Expected final status:
Expected executed steps:
```

### Scenario B — policy question

Use a return/policy question supplied by your instructor.

Prediction:

```text
Expected lookup(s):
Expected final status:
Expected executed steps:
```

### Scenario C — missing trusted information

Use a scenario where analysis requires context that cannot be verified.

Prediction:

```text
Expected lookup(s):
Expected final status:
Expected executed steps:
```

---

# Deliverable

Be ready to show one scenario with:

```text
your pseudocode
predicted steps
actual executed_steps
final ticket status
trusted context used
```

Then answer:

> **Who chose the order of operations in this workflow?**

And:

> **Which decisions did Claude assist with, and which decisions remained under application control?**

---

# Optional challenge

If your workflow is working, test a request where both:

```text
needs_order_lookup = true
needs_faq_lookup = true
```

Discuss whether those independent lookups could technically be executed concurrently and whether changing the implementation is worth the added complexity for this training application.

Do not change the workflow architecture unless the required behaviour is already correct.
