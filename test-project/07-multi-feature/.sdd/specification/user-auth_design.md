---
id: design-user-auth
type: design
title: "User Auth Design"
feature-id: user-auth
status: draft
created: 2026-02-26
updated: 2026-02-26
sdd-phase: plan
impl-status: not-implemented
depends-on: [spec-user-auth]
tags: [security, architecture]
---

# User Auth Design

## Architecture

- bcrypt for password hashing
- JWT with RS256 signing
- Redis for token blacklist
- Rate limiting on auth endpoints

## Database Schema

- users: id, email, password_hash, totp_secret, created_at
- sessions: id, user_id, token_hash, expires_at
