### 1. /enroll
- **Method:** POST  
- **Description:** Register a new voter.  
- **Request Example:**
```json
{
  "aadhaar_number": "123456789012",
  "fingerprint": "base64encodeddata"
}
```
- **Response Example:**
```json
{
  "status": "success",
  "message": "Voter enrolled successfully"
}
```

### 2. /verify
- **Method:** POST  
- **Description:** Verify a voter's identity before voting.  
- **Request Example:**
```json
{
  "aadhaar_number": "123456789012",
  "fingerprint": "base64encodeddata"
}
```
- **Response Example:**
```json
{
  "status": "verified",
  "message": "Voter verified successfully"
}
```

### 3. /vote
- **Method:** POST  
- **Description:** Cast a vote for a candidate.  
- **Request Example:**
```json
{
  "aadhaar_number": "123456789012",
  "candidate_id": "CAND123"
}
```
- **Response Example:**
```json
{
  "status": "success",
  "message": "Vote cast successfully"
}
```

### 4. /device/heartbeat
- **Method:** GET  
- **Description:** Check the health/status of voting devices.  
- **Response Example:**
```json
{
  "device_id": "DEV001",
  "status": "online",
  "last_seen": "2025-09-14T16:00:00Z"
}
```

### 5. /admin/metrics
- **Method:** GET  
- **Description:** Fetch system metrics for admin monitoring.  
- **Response Example:**
```json
{
  "total_votes": 1050,
  "active_devices": 12,
  "alerts": []
}
```

