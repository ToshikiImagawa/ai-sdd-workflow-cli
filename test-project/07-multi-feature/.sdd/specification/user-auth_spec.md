---
id: spec-user-auth
type: spec
title: "User Auth Specification"
feature-id: user-auth
status: draft
created: 2026-02-26
updated: 2026-02-26
sdd-phase: specify
depends-on: [prd-user-auth]
tags: [security, api]
---

# User Auth Specification

## Authentication Flow

1. User submits credentials
2. Server validates and issues JWT
3. Client stores token
4. Token refresh on expiry

## API

- POST /api/auth/login
- POST /api/auth/register
- POST /api/auth/refresh
- POST /api/auth/logout
- POST /api/auth/2fa/setup
- POST /api/auth/2fa/verify
