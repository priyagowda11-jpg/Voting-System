# API Design (Voting Prototype)

## Overview
This document describes the backend API for the `voting-proto` project.
Base path: `/api/v1`

## Authentication
- Each device uses an API key.
- Requests must include header:

- - All request and response bodies use `application/json`.

## Conventions
- Timestamps: ISO 8601 UTC (example: `2025-09-24T18:15:30Z`)
- IDs: `local_voter_id`, `fingerprint_id`, `candidate_id` are strings (alphanumeric)
- Error format:
```json
{ "status": "error", "code": "CODE", "message": "Human readable message" }

{
  "local_voter_id": "VOT123",
  "name": "Arjun Kumar",
  "dob": "1999-05-15",
  "fingerprint_id": "FPX12",
  "constituency": "Bangalore North",
  "mobile_masked": "98******45"   // optional
}

{ "status": "success", "message": "Voter enrolled" }

INSERT INTO voters (local_voter_id, name, dob, constituency, fingerprint_id, voted_flag, mobile_masked)
VALUES (?, ?, ?, ?, ?, 0, ?);

{ "device_id": 1, "fingerprint_id": "FPX12" }

{
  "status": "verified",
  "local_voter_id": "VOT123",
  "name": "Arjun Kumar",
  "voted_flag": false
}

{ "status": "failed", "reason": "Fingerprint mismatch" }

{
  "device_id": 1,
  "local_voter_id": "VOT123",
  "candidate_id": "CAND45"
}

{ "status": "success", "message": "Vote recorded" }

{ "status": "failed", "reason": "Voter already voted" }
BEGIN TRANSACTION;

UPDATE voters
SET voted_flag = 1
WHERE local_voter_id = ? AND voted_flag = 0;

-- check that update affected 1 row; if 0 => already voted -> ROLLBACK and return 409

INSERT INTO votes (local_voter_id, candidate_id, timestamp, station_id)
VALUES (?, ?, CURRENT_TIMESTAMP, ?);

INSERT INTO events (local_voter_id, device_id, result, timestamp)
VALUES (?, ?, 'vote_success', CURRENT_TIMESTAMP);

COMMIT;

{ "device_id": 1, "status": "online" }

{ "status": "ok", "last_seen": "2025-09-24T18:15:30Z" }

UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE device_id = ?;

{
  "total_voters": 50,
  "votes_cast": 20,
  "turnout_percentage": 40,
  "active_devices": 4,
  "alerts": 2
}

SELECT COUNT(*) FROM voters;
SELECT COUNT(*) FROM votes;
SELECT COUNT(*) FROM devices WHERE last_seen > datetime('now', '-5 minutes');
SELECT COUNT(*) FROM alerts WHERE timestamp > datetime('now', '-1 day');




