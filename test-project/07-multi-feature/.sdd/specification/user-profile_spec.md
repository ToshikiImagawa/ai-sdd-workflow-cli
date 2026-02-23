---
title: "User Profile Specification"
feature-id: user-profile
tags: [user, api]
depends_on: [user-profile]
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
