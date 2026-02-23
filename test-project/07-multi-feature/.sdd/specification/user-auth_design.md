---
title: "User Auth Design"
feature-id: user-auth
tags: [security, architecture]
depends_on: [user-auth]
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
