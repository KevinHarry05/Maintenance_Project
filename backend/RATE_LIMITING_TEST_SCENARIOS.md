# Login Rate Limiting - Test Scenarios & Examples

## Quick Testing Guide

### Prerequisites
- Backend running on `http://localhost:8000`
- Redis running on `redis://localhost:6379/0`
- Valid test user registered with credentials

---

## Test Setup

### Register Test User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "TestPassword123",
    "role": "user"
  }'
```

---

## Scenario 1: Successful Login (Rate Limit Resets)

### Expected Behavior
- User logs in with correct credentials
- Rate limit counter is reset to 0
- Receives access token
- Can immediately attempt another login

### Test Steps
```bash
# Attempt 1: Successful login with valid credentials
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123"

# Response should be:
# HTTP 200 OK
# {
#   "access_token": "eyJhbGc...",
#   "token_type": "bearer"
# }

# Rate limit counter is now RESET to 0
```

### Verification
✅ HTTP 200 status  
✅ Access token provided  
✅ Rate limit counter in Redis deleted  

---

## Scenario 2: Brute Force Protection (5 Failed Attempts)

### Expected Behavior
- Each invalid credentials attempt increments counter
- After 5 failed attempts within 60 seconds, rate limit is enforced
- 6th attempt returns HTTP 429

### Test Steps
```bash
# Attempts 1-5: Invalid password
for i in {1..5}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@example.com&password=WrongPassword123"
  # Response: HTTP 401 Unauthorized (each time)
done

# Attempt 6: Still invalid (should be rate limited)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=WrongPassword123" \
  -i  # Include headers

# Response should be:
# HTTP 429 Too Many Requests
# Retry-After: 45
# {
#   "detail": "Too many login attempts. Please try again later."
# }
```

### Verification
✅ First 5 attempts return HTTP 401  
✅ Attempt 6 returns HTTP 429  
✅ Retry-After header present  
✅ Error message clear and actionable  

---

## Scenario 3: Failed Then Successful Login

### Expected Behavior
- 1 failed attempt increments counter to 1
- Successful login attempts during same window
- Rate limit counter resets after successful login
- Can continue using the service

### Test Steps
```bash
# Attempt 1: Invalid credentials
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=WrongPassword123"
# Response: HTTP 401
# Counter in Redis: 1/5

# Attempt 2: Valid credentials
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123"
# Response: HTTP 200 with access token
# Counter in Redis: DELETED (reset)

# Attempt 3: Can login again (counter was reset)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123"
# Response: HTTP 200 with access token
```

### Verification
✅ Rate limit resets after successful login  
✅ Can immediately login again  
✅ Counter tracking accurate  

---

## Scenario 4: Multiple Independent IPs

### Expected Behavior
- Each IP address tracked independently
- Rate limit on one IP doesn't affect another
- Perfect for distributed attack scenarios

### Test Steps
```bash
# From IP 192.168.1.100:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -d "username=test@example.com&password=WrongPassword123"
# Counter for 192.168.1.100: 1/5

# From IP 192.168.1.101:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Forwarded-For: 192.168.1.101" \
  -d "username=test@example.com&password=WrongPassword123"
# Counter for 192.168.1.101: 1/5

# Each IP has independent counter
# 192.168.1.100 can still make 4 more attempts
# 192.168.1.101 can still make 4 more attempts
```

### Verification
✅ Each IP has independent counter  
✅ Rate limit on one IP doesn't block another  
✅ Counters tracked in Redis as separate keys  

---

## Scenario 5: Rate Limit Window Reset (60 seconds)

### Expected Behavior
- Counter persists for 60 seconds (by default)
- After 60 seconds, counter automatically expires
- Can attempt login again from same IP

### Test Steps
```bash
# At T=0: 5 failed attempts
for i in {1..5}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@example.com&password=WrongPassword123"
done
# Rate limited at attempt 6

# At T=61 (wait 61 seconds):
# Redis key expires automatically

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123"
# Response: HTTP 200 with access token
# Counter resets (expired)
```

### Verification
✅ Counter expires after window (60 sec default)  
✅ Can attempt login again after expiration  
✅ Automatic cleanup of stale data  

---

## Scenario 6: Proxy Header Support

### Expected Behavior
- Rate limiter extracts IP from X-Forwarded-For header
- Handles load balancer/proxy scenarios
- Falls back to direct IP if header missing

### Test Steps
```bash
# With X-Forwarded-For header (typical proxy scenario)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Forwarded-For: 203.0.113.42, 198.51.100.178" \
  -d "username=test@example.com&password=WrongPassword123"
# Uses first IP from header: 203.0.113.42

# With X-Real-IP header (alternative proxy header)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Real-IP: 203.0.113.42" \
  -d "username=test@example.com&password=WrongPassword123"
# Uses IP from X-Real-IP: 203.0.113.42

# Without proxy headers (direct connection)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=WrongPassword123"
# Uses client.host from connection: 127.0.0.1 or actual IP
```

### Verification
✅ X-Forwarded-For header parsed correctly  
✅ X-Real-IP header recognized  
✅ Direct connection IP used as fallback  
✅ First IP in list extracted from X-Forwarded-For  

---

## Scenario 7: Rate Limit Configuration Changes

### Expected Behavior
- Limits configurable via environment variables
- Changes apply on next restart
- Default: 5 attempts per 60 seconds

### Configuration Examples

#### Strict Mode (Testing)
```bash
# .env
LOGIN_RATE_LIMIT_PER_MINUTE=2
LOGIN_RATE_LIMIT_WINDOW_SECONDS=30
```

#### Lenient Mode (Corporate Network)
```bash
# .env
LOGIN_RATE_LIMIT_PER_MINUTE=10
LOGIN_RATE_LIMIT_WINDOW_SECONDS=120
```

### Test Steps
```bash
# Set strict limits in .env:
# LOGIN_RATE_LIMIT_PER_MINUTE=2

# Restart application

# Attempt 1-2: Invalid (allowed)
for i in {1..2}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@example.com&password=WrongPassword123"
done

# Attempt 3: Blocked (rate limit exceeded)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=WrongPassword123" \
  -i
# HTTP 429
```

### Verification
✅ Configuration loaded from environment  
✅ Custom limits enforced  
✅ Changes effective after restart  

---

## Scenario 8: Graceful Degradation (Redis Unavailable)

### Expected Behavior
- If Redis is down, login still works
- Warning logged about rate limiting being unavailable
- Security: allows logins to maintain service availability

### Test Steps
```bash
# Stop Redis:
# redis-cli shutdown

# Attempt login:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123"

# Response: HTTP 200 with access token (works!)
# Check logs: "WARNING: Redis error... Allowing login (graceful degradation)"

# Restart Redis:
# redis-server

# Verify rate limiting works again
```

### Verification
✅ Login succeeds even if Redis unavailable  
✅ Warning logged appropriately  
✅ Normal rate limiting resumes when Redis is back  
✅ No data loss or corruption  

---

## Monitoring & Debugging

### Check Rate Limit Counter in Redis
```bash
redis-cli

# View all rate limit keys:
> KEYS login_rate_limit:*

# Check specific IP:
> GET login_rate_limit:192.168.1.100

# Check TTL (time remaining):
> TTL login_rate_limit:192.168.1.100

# Check success markers:
> KEYS login_success:*

# Clear all rate limiting data (for testing):
> DEL login_rate_limit:*
> DEL login_success:*
```

### View Application Logs
```bash
# Monitor logs in real-time:
tail -f api-codex.log

# Search for rate limiting events:
grep "rate_limit" api-codex.log
grep "login_rate_limit" api-codex.log
```

### Log Patterns

**Failed Attempt**:
```
Recorded failed login attempt for IP: 192.168.1.100, attempts: 1/5
```

**Rate Limit Exceeded**:
```
Login rate limit exceeded for IP: 192.168.1.100, attempts: 5/5
```

**Rate Limit Reset**:
```
Reset login rate limit for IP: 192.168.1.100
```

**Redis Error**:
```
Redis error during login rate limit check for IP 192.168.1.100: Connection refused
```

---

## Common Issues & Solutions

### Issue: Always Getting Rate Limited

**Solution**:
1. Clear Redis: `redis-cli DEL login_rate_limit:*`
2. Check IP extraction: Look for "Recorded failed login attempt" logs
3. Verify rate limit config is correct
4. Restart application to reload config

### Issue: Rate Limiting Not Working

**Solution**:
1. Verify Redis is running: `redis-cli ping` → `PONG`
2. Check `REDIS_URL` in `.env`
3. Verify `LOGIN_RATE_LIMIT_PER_MINUTE > 0`
4. Check application startup logs for Redis connection errors

### Issue: Users on Same Network Affected

**Solution**:
- This is expected behavior (same IP tracked together)
- Increase `LOGIN_RATE_LIMIT_PER_MINUTE` in `.env`
- Consider user-based rate limiting in future updates

### Issue: X-Forwarded-For Not Working

**Solution**:
1. Ensure proxy is configured to send header
2. Verify header format: `IP1, IP2, ...`
3. Check logs to confirm IP extraction
4. Fallback to `X-Real-IP` or direct IP will work

---

## Performance Considerations

### Latency Impact
- Redis operation: ~1-2ms
- No database queries for rate limiting
- Negligible impact on login response time

### Redis Memory Usage
- Per IP entry: ~60 bytes
- With 10,000 active IPs: ~600KB
- Auto-cleanup: Keys expire after window

### Throughput
- Supports thousands of concurrent login attempts
- Limited only by Redis/network capacity
- No blocking operations

---

## Security Best Practices

✅ **Always use HTTPS** in production to prevent IP spoofing  
✅ **Monitor rate limit events** for attack patterns  
✅ **Set appropriate limits** based on your user base  
✅ **Test with proxy headers** if behind load balancer  
✅ **Keep Redis secure** (bind to localhost, use password)  
✅ **Log all rate limit events** for audit trail  

---

## Next Steps

1. **Deploy**: Follow deployment checklist in RATE_LIMITING_IMPLEMENTATION.md
2. **Monitor**: Watch logs for rate limiting events and Redis errors
3. **Tune**: Adjust limits based on real-world usage patterns
4. **Document**: Share these scenarios with support team
5. **Enhance**: Consider future improvements (user-based, geo-blocking, etc.)
