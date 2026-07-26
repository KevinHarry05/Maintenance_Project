# Login Rate Limiting Implementation Guide

## Overview
This document describes the implementation of **HIGH PRIORITY ISSUE #2: Login Rate Limiting** for the SMBS API.

The implementation adds IP-based rate limiting to the `/auth/login` endpoint to prevent brute force attacks. Redis is used for efficient, distributed rate limit tracking.

---

## Features

✅ **IP-Based Rate Limiting**: Tracks login attempts per IP address  
✅ **Configurable Limits**: Maximum attempts and time window configurable via environment variables  
✅ **HTTP 429 Response**: Returns proper "Too Many Requests" status code when limit exceeded  
✅ **Retry-After Header**: Clients receive guidance on when to retry  
✅ **Failed Attempt Tracking**: Increments counter only on failed login attempts  
✅ **Successful Login Reset**: Clears rate limit counter after successful login  
✅ **Graceful Degradation**: If Redis is unavailable, login is allowed with warning logged  
✅ **Proxy Support**: Handles X-Forwarded-For and X-Real-IP headers for proxy scenarios  
✅ **Zero Breaking Changes**: Existing login functionality and schemas unchanged  

---

## Architecture

### Components

#### 1. **LoginRateLimiter Class** (`app/core/login_rate_limiter.py`)
Core rate limiting engine with three main methods:

- `check_rate_limit(request)`: Validates if client has exceeded rate limit
- `record_failed_attempt(request)`: Increments failed attempt counter
- `reset_limit(request)`: Clears rate limit after successful login

**Redis Key Format**:
- Rate limit key: `login_rate_limit:{ip_address}`
- Success marker: `login_success:{ip_address}` (for audit purposes)

#### 2. **Configuration** (`app/config.py`)
New settings with sensible defaults:
```python
LOGIN_RATE_LIMIT_PER_MINUTE: int = 5  # Max failed attempts
LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60  # Time window
```

#### 3. **Auth Route Integration** (`app/routes/auth.py`)
Updated `/auth/login` endpoint to:
1. Check rate limit before processing login
2. Record failed attempts on invalid credentials
3. Reset rate limit on successful login
4. Return HTTP 429 with Retry-After header when limit exceeded

---

## Configuration

### Environment Variables

Add to `.env` file (example values provided):

```
# Login Rate Limiting Configuration
LOGIN_RATE_LIMIT_PER_MINUTE=5           # Maximum failed login attempts per minute
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60      # Rate limiting window in seconds
```

### Default Values

| Setting | Default | Description |
|---------|---------|-------------|
| `LOGIN_RATE_LIMIT_PER_MINUTE` | 5 | Max failed attempts per IP per window |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | 60 | Time window for rate limiting (seconds) |

### Customization Examples

**Strict Policy** (2 attempts per 30 seconds):
```
LOGIN_RATE_LIMIT_PER_MINUTE=2
LOGIN_RATE_LIMIT_WINDOW_SECONDS=30
```

**Lenient Policy** (10 attempts per 2 minutes):
```
LOGIN_RATE_LIMIT_PER_MINUTE=10
LOGIN_RATE_LIMIT_WINDOW_SECONDS=120
```

---

## How It Works

### Normal Login Flow

```
Client Request
    ↓
1. Extract Client IP (with proxy support)
    ↓
2. Check Rate Limit
    - If exceeded: Return HTTP 429 with Retry-After header
    - If OK: Continue to step 3
    ↓
3. Validate Credentials
    - Invalid: Record failed attempt, return HTTP 401
    - Valid: Reset rate limit, return access token
```

### Rate Limit Check

1. **Pre-Login Check**: Before database query
   - Extracts client IP from request
   - Queries Redis for current attempt count
   - Returns HTTP 429 if limit exceeded

2. **Failed Attempt Recording**: On invalid credentials
   - Increments rate limit key in Redis
   - Sets TTL to window duration (60 seconds)
   - Logs the failed attempt

3. **Successful Login Reset**: After credentials validated
   - Deletes rate limit key
   - Sets success marker for audit trail
   - Logs the reset

### Client IP Resolution

Supports multiple sources (in priority order):
1. `X-Forwarded-For` header (proxy pass-through)
2. `X-Real-IP` header (alternative proxy header)
3. `request.client.host` (direct connection IP)
4. Falls back to `"unknown"` if unavailable

---

## Error Handling

### HTTP 429 Response Format

When rate limit exceeded:

```json
HTTP/1.1 429 Too Many Requests
Retry-After: 45

{
  "detail": "Too many login attempts. Please try again later."
}
```

The `Retry-After` value indicates seconds until the rate limit resets.

### Redis Unavailability

If Redis connection fails during rate limit check:
- Login is **allowed** (graceful degradation)
- Warning is logged
- Normal operation continues
- Ensures service availability over strict enforcement

Log entry example:
```
WARNING: Redis error during login rate limit check for IP 192.168.1.100: Connection refused. 
Allowing login (graceful degradation)
```

---

## Files Modified/Created

### Created
- `backend/app/core/login_rate_limiter.py` - Core rate limiter implementation

### Modified
- `backend/app/routes/auth.py` - Integrated rate limiting into /auth/login
- `backend/app/config.py` - Added LOGIN_RATE_LIMIT_* settings
- `backend/.env.example` - Added configuration examples

---

## Integration Points

### Dependencies
- **Redis**: Already configured in project (via `REDIS_URL`)
- **FastAPI**: Request object for IP extraction
- **Pydantic Settings**: Configuration management

### No Breaking Changes
- ✅ Existing login endpoint signature compatible
- ✅ Request/response schemas unchanged
- ✅ Other endpoints unaffected
- ✅ Database unchanged
- ✅ Backward compatible behavior

---

## Test Scenarios

### Scenario 1: Successful Login
```
Request 1: Valid credentials
→ Check rate limit: OK (0 attempts)
→ Validate credentials: PASS
→ Reset rate limit counter
→ Response: HTTP 200 with access token
```

### Scenario 2: Brute Force Attack
```
Request 1-5: Invalid credentials
→ Failed attempt recorded: attempts = 1, 2, 3, 4, 5
→ Response: HTTP 401

Request 6: Invalid credentials
→ Rate limit check: FAIL (5/5 attempts reached)
→ Response: HTTP 429 with Retry-After: 60

Requests 7+: (within 60 seconds)
→ Rate limit check: FAIL
→ Response: HTTP 429 with Retry-After: XX
```

### Scenario 3: Failed Then Successful Login
```
Request 1: Invalid credentials
→ Failed attempt recorded: attempts = 1
→ Response: HTTP 401

Request 2: Valid credentials
→ Rate limit check: OK (1 attempt < 5)
→ Validate credentials: PASS
→ Reset rate limit counter (delete Redis key)
→ Response: HTTP 200 with access token

Request 3: Invalid credentials (fresh attempt)
→ Rate limit check: OK (counter was reset)
→ Response: HTTP 401 (attempts = 1)
```

### Scenario 4: Redis Unavailable
```
Request 1-N: Any credentials
→ Rate limit check: Redis error
→ Log warning about graceful degradation
→ Continue with normal login flow (no rate limiting)
→ Response: Normal HTTP 200 or 401
```

### Scenario 5: Multiple IPs
```
IP 192.168.1.100: 5 failed attempts → Rate limited
IP 192.168.1.101: 1 failed attempt → Can continue
→ Each IP tracked independently
```

---

## Security Considerations

### Brute Force Protection
- Limits failed attempts per IP to 5/minute (default)
- Prevents dictionary attacks
- Window resets automatically

### Distributed Attacks
- Per-IP tracking prevents distributed attacks from affecting one IP
- Proxy support ensures accurate IP detection

### Denial of Service
- Rate limiting applies only to login endpoint
- Other endpoints unaffected
- Legitimate users reset counter on successful login
- Graceful degradation if Redis fails

### Credentials Protection
- Failed attempts logged with IP only (no username/password)
- No rate limit data persisted permanently
- Redis keys auto-expire

---

## Monitoring & Logging

### Log Events

**Failed Attempt Recording**:
```
INFO: Recorded failed login attempt for IP: 192.168.1.100, attempts: 1/5
```

**Rate Limit Exceeded**:
```
WARNING: Login rate limit exceeded for IP: 192.168.1.100, attempts: 5/5
```

**Rate Limit Reset**:
```
INFO: Reset login rate limit for IP: 192.168.1.100
```

**Redis Error**:
```
WARNING: Redis error while recording failed login attempt for IP 192.168.1.100: Connection refused
```

### Metrics to Track
- Failed login attempts by IP
- Rate limit exceeded events
- Rate limit resets (successful logins)
- Redis availability

---

## Deployment Checklist

- [ ] Verify Redis is running and accessible
- [ ] Set environment variables in `.env`:
  - `LOGIN_RATE_LIMIT_PER_MINUTE=5`
  - `LOGIN_RATE_LIMIT_WINDOW_SECONDS=60`
- [ ] Test login with valid credentials (should reset counter)
- [ ] Test login with invalid credentials multiple times (should be rate limited)
- [ ] Verify HTTP 429 response with Retry-After header
- [ ] Monitor logs for rate limiting events
- [ ] Verify other endpoints are unaffected
- [ ] Test with proxy headers (X-Forwarded-For)

---

## Future Enhancements

Potential improvements for future iterations:

1. **User-Based Rate Limiting**: Track by username instead of just IP
2. **Adaptive Thresholds**: Adjust limits based on login patterns
3. **Geo-Blocking**: Block suspicious geographic patterns
4. **Alerting**: Send alerts on repeated rate limit violations
5. **Whitelist**: Configure trusted IPs that bypass rate limiting
6. **Custom Response**: Customize rate limit error messages
7. **Metrics Export**: Prometheus metrics for monitoring

---

## Support & Troubleshooting

### Rate Limit Not Working
- Check Redis is running: `redis-cli ping` → should respond `PONG`
- Verify `REDIS_URL` in `.env` is correct
- Check application logs for Redis errors
- Ensure `LOGIN_RATE_LIMIT_PER_MINUTE` > 0

### Always Getting Rate Limited
- Check if Redis data is stale: `redis-cli GET login_rate_limit:*`
- Verify IP extraction is correct (check logs)
- Ensure proper rate limit configuration
- Clear Redis: `redis-cli FLUSHDB` (for testing only)

### False Positives on Shared Network
- Check if multiple users share same IP
- Adjust `LOGIN_RATE_LIMIT_PER_MINUTE` to higher value
- Consider user-based rate limiting in future

---

## References

- [HTTP 429 Status Code](https://tools.ietf.org/html/rfc6585#section-4)
- [Retry-After Header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After)
- [OWASP: Brute Force Protection](https://owasp.org/www-community/attacks/Brute_force_attack)
- [Redis Rate Limiting Patterns](https://redis.io/commands/incr)

---

## Version History

**v1.0** - Initial implementation
- IP-based rate limiting for login endpoint
- Configurable limits via environment variables
- Redis backend integration
- Graceful degradation on Redis failure
- Retry-After header support
