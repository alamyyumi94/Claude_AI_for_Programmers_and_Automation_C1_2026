# Exercise 01 — Secure Order Lookup

## Goal

Implement an order lookup that returns an order only when it belongs to the
current customer.

## Time

Approximately 20 minutes.

## Starting point

The application is connected to MongoDB.

You have:

```text
app/schemas/order.py
app/repositories/order_repository.py
```

The repository method is incomplete.

## Business requirement

SupportOps must retrieve order details for a support request.

Knowing an `order_id` alone must not allow a caller to retrieve another
customer's order.

## Task

Implement:

```text
OrderRepository.get_order_for_customer(...)
```

Use the existing method arguments, projection, and `OrderContext` model.

**Before coding**, write down the MongoDB query your pair believes is correct.

Your implementation should:

- query by both `customer_id` and `order_id`;
- use the existing projection;
- return an `OrderContext` when an authorized record exists;
- return `None` when no authorized record exists.

## Expected behaviour

The same `order_id` must not be retrievable under a different customer ID.

## Questions

1. Why is the customer identifier part of the lookup?
2. Why does the repository use a projection?
3. Should Claude decide whether a customer may access a different order?
4. What should the repository return when no authorized order is found?

## Deliverable

Show the query your pair chose and explain why it enforces the business
requirement.
