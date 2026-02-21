---
title: "Checkout Specification"
feature-id: checkout
tags: [commerce]
depends_on: [checkout, cart]
---

# Checkout Specification

## Checkout Steps

1. Shipping address
2. Payment method
3. Order review
4. Confirmation

## API

- POST /api/checkout/start
- PUT /api/checkout/:id/shipping
- PUT /api/checkout/:id/payment
- POST /api/checkout/:id/confirm
