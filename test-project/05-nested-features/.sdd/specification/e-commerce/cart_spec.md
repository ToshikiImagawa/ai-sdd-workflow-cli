---
id: spec-cart
type: spec
title: "Cart Specification"
feature-id: cart
status: draft
created: 2026-02-26
updated: 2026-02-26
sdd-phase: specify
depends-on: [prd-cart]
tags: [commerce]
---

# Cart Specification

## Data Model

- CartItem: product_id, quantity, price
- Cart: items[], total, currency

## API

- GET /api/cart
- POST /api/cart/items
- DELETE /api/cart/items/:id
- PUT /api/cart/items/:id
