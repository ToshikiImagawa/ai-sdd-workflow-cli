---
id: spec-checkout
type: spec
title: "Checkout Specification"
feature-id: checkout
status: draft
created: 2026-02-26
updated: 2026-02-26
sdd-phase: specify
depends-on: [prd-checkout, spec-cart]
tags: [commerce]
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
