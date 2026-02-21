---
title: "Notification Specification"
feature-id: notification
tags: [messaging]
depends_on: [notification]
---

# Notification Specification

## Architecture

- WebSocket for realtime delivery
- Queue-based processing for email/push

## API

- GET /api/notifications
- POST /api/notifications/read
- PUT /api/notifications/preferences
