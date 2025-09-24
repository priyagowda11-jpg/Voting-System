
## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Conventions](#conventions)
- [Endpoints](#endpoints)
  - [Enroll voter](#1-enroll-voter)
  - [Verify voter](#2-verify-voter)
  - [Cast vote](#3-cast-vote)
  - [Device heartbeat](#4-device-heartbeat)
  - [Admin metrics](#5-admin-metrics)


This is optional but makes your README/API doc more professional.# API Design (Voting Prototype)

## Overview 

This document describes the backend API for the voting-proto project.  
`Base path: /api/v1`

## Authentication
- Each device uses an API key.  
- All requests must include this header:

```
Authorization: ApiKey <api_key>
```

- All request and response bodies are in JSON (application/json) 

## Conventions
- **Timestamps:** ISO 8601 UTC (example: `2025-09-24T18:15:30Z`)  
- **IDs:** `local_voter_id`, `fingerprint_id`, `candidate_id` are strings (alphanumeric)  
- **Error format:**
```json
{
  "status": "error",
  "code": "CODE",
  "message": "Human readable message"
}
```


HTTP status codes: 200, 201, 400, 401, 403, 404, 409, 500

## Endpoints 

1. Enroll voter

POST /api/v1/enroll — Add a new voter.

Request
```json
{
  "local_voter_id": "VOT123",
  "name": "Arjun Kumar",
  "dob": "1999-05-15",
  "fingerprint_id": "FPX12",
  "constituency": "Bangalore North",
  "mobile_masked": "98******45"
}
```
Response (success)
```json
{ "status": "success", "message": "Voter enrolled" }

```
Response (error)
```json
{ "status": "error", "message": "Already exists" }
```
DB action
```sql
INSERT INTO voters (local_voter_id, name, dob, constituency, fingerprint_id, voted_flag, mobile_masked)
VALUES (?, ?, ?, ?, ?, 0, ?);
```

2. Verify voter

POST /api/v1/verify — Check fingerprint and return voter info.

Request
```json
{ "device_id": 1, "fingerprint_id": "FPX12" }
```
Response (verified)
```json
{
  "status": "verified",
  "local_voter_id": "VOT123",
  "name": "Arjun Kumar",
  "voted_flag": false
}
```
Response (failed)
```json
{ "status": "failed", "reason": "Fingerprint mismatch" }
```
3. Cast vote

POST /api/v1/vote — Record vote.

Request
```json
{
  "device_id": 1,
  "local_voter_id": "VOT123",
  "candidate_id": "CAND45"
}
```

Response (success)
```json
{ "status": "success", "message": "Vote recorded" }
```
Response (error — already voted)
```json
{ "status": "failed", "reason": "Voter already voted" }
```
DB atomic transaction
```sql
BEGIN TRANSACTION;

UPDATE voters
SET voted_flag = 1
WHERE local_voter_id = ? AND voted_flag = 0;

-- if 0 rows affected -> already voted -> ROLLBACK and return error

INSERT INTO votes (local_voter_id, candidate_id, timestamp, station_id)
VALUES (?, ?, CURRENT_TIMESTAMP, ?);

INSERT INTO events (local_voter_id, device_id, result, timestamp)
VALUES (?, ?, 'vote_success', CURRENT_TIMESTAMP);

COMMIT;
```

4. Device heartbeat

POST /api/v1/device/heartbeat — Keep device online.

Request
```json
{ "device_id": 1, "status": "online" }
```

Response
```json
{ "status": "ok", "last_seen": "2025-09-24T18:15:30Z" }
```
DB action
```sql
UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE device_id = ?;
```
5. Admin metrics

GET /api/v1/admin/metrics — Admin-only: fetch system stats.

Response
```json
{
  "total_voters": 50,
  "votes_cast": 20,
  "turnout_percentage": 40,
  "active_devices": 4,
  "alerts": 2
}
```
SQL queries example
```sql
SELECT COUNT(*) FROM voters;
SELECT COUNT(*) FROM votes;
SELECT COUNT(*) FROM devices WHERE last_seen > datetime('now', '-5 minutes');
SELECT COUNT(*) FROM alerts WHERE timestamp > datetime('now','-1 day');
```
