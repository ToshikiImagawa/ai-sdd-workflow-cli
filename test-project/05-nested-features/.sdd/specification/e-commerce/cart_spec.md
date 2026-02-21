---
title: "Cart Specification"
feature-id: cart
tags: [commerce]
depends_on: [cart]
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
