---
id: spec-user-profile
type: spec
title: "User Profile Specification"
feature-id: user-profile
status: draft
created: 2026-02-26
updated: 2026-02-26
sdd-phase: specify
depends-on: [prd-user-profile]
tags: [user, api]
---

# User Profile Specification

## Data Model

- User: id, email, name, avatar_url, bio, created_at
- UserSettings: user_id, theme, locale, notifications

## API

- GET /api/profile
- PUT /api/profile
- POST /api/profile/avatar
- DELETE /api/profile
- GET /api/profile/settings
- PUT /api/profile/settings
