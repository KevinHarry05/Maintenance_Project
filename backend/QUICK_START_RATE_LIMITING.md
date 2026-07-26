# Login Rate Limiting - Quick Start Guide

## TL;DR - 30 Seconds

✅ **What's New**: Login endpoint now has IP-based rate limiting  
✅ **Default Limits**: 5 failed attempts per minute per IP  
✅ **HTTP Status**: Returns 429 when limit exceeded  
✅ **Header**: Includes `Retry-After` with retry time  
✅ **Auto-Reset**: Counter clears after successful login  
✅ **Redis**: Uses existing Redis configuration  

---

## Configuration (Optional)

Add to `.env` if you want to change defaults:

```bash
LOGIN_RATE_LIMIT_PER_MINUTE=5           # Max attempts (default: 5)
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60      # Time window (default: 60)
```

**No changes needed** - defaults are production-ready!

---

## How It Works

### Successful Login ✅
```
User tries to login with correct credentials
→ Rate limit check: PASS (0 failed attempts)
→ Credentials validated
→ Counter reset to 0
→ Return access token
```

### Failed Logins ❌
```
User tries with wrong password (Attempts 1-5)
→ Each attempt: Rate limit PASS, credentials FAIL, counter increments
→ Response: HTTP 401 (unauthorized)

User tries again (Attempt 6)
→ Rate limit CHECK: FAIL (5 attempts reached)
→ Response: HTTP 429 Too Many Requests
→ Header: Retry-After: 45 (wait 45 seconds)
```

---

## Testing

### Test Successful Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=ValidPassword123"

# Expected: HTTP 200 with access token
```

### Test Rate Limiting
```bash
# Fail 5 times
for i in {1..5}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=user@example.com&password=WrongPassword123"
  # Each returns: HTTP 401
done

# Try 6th time
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=WrongPassword123" \
  -i

# Expected: HTTP 429 with Retry-After header
```

---

## Monitoring

### Check Logs
```bash
tail -f api-codex.log | grep rate_limit
```

### Log Examples
```
INFO: Recorded failed login attempt for IP: 192.168.1.100, attempts: 1/5
INFO: Recorded failed login attempt for IP: 192.168.1.100, attempts: 2/5
WARNING: Login rate limit exceeded for IP: 192.168.1.100, attempts: 5/5
INFO: Reset login rate limit for IP: 192.168.1.100
```

### Check Redis
```bash
redis-cli

# View active rate limits
> KEYS login_rate_limit:*

# Check specific IP
> GET login_rate_limit:192.168.1.100

# View time remaining
> TTL login_rate_limit:192.168.1.100
```

---

## Deployment

### Prerequisites
- Redis running: `redis-cli ping` → `PONG`
- Update `.env` with rate limit settings (optional)
- Restart application

### Verification
```bash
# Test successful login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=CorrectPassword"

# Should work normally
# HTTP 200 with access token

# Test rate limiting
# Make 5 failed attempts, 6th should return HTTP 429
```

---

## Key Features

| Feature | Details |
|---------|---------|
| **Tracking** | Per IP address (handles proxies) |
| **Limit** | 5 failed attempts per minute |
| **Status Code** | HTTP 429 Too Many Requests |
| **Retry Header** | Retry-After with seconds |
| **Reset** | Automatic on successful login |
| **Config** | Via environment variables |
| **Storage** | Redis (existing setup) |
| **Failure Mode** | Allows login if Redis down |

---

## What Changed

### Backend Code
- ✅ New file: `app/core/login_rate_limiter.py`
- ✅ Updated: `app/routes/auth.py` (integrated rate limiting)
- ✅ Updated: `app/config.py` (added settings)
- ✅ Updated: `.env.example` (documented settings)

### API Behavior
- ✅ `/auth/login` now enforces rate limiting
- ⚠️ **New Response**: HTTP 429 when rate limited
- ✅ No other changes to endpoint
- ✅ Request/response schemas unchanged

### Database
- ✅ No changes (uses Redis instead)

---

## Troubleshooting

### Symptoms: User always rate limited

**Check**:
1. Is Redis running? `redis-cli ping`
2. Correct IP? Check logs for "Recorded failed login attempt"
3. Correct password? Should get HTTP 401 first
4. Cache stale? Try: `redis-cli DEL login_rate_limit:*`

### Symptoms: Rate limiting not working

**Check**:
1. Redis connected? Check startup logs
2. Config correct? Check `.env` values
3. HTTP 429 response? Test with curl -i
4. Restart app after .env changes

### Symptoms: Users on same network affected

**This is normal** - same IP = shared limit

**Solutions**:
- Increase `LOGIN_RATE_LIMIT_PER_MINUTE`
- Tell users to wait 60 seconds and retry
- User-based rate limiting (future feature)

---

## FAQ

**Q: Will this break existing logins?**  
A: No! Successful logins work normally. Limit only applies to 5+ failed attempts.

**Q: What if Redis is down?**  
A: Login still works. Warning logged. No rate limiting until Redis recovers.

**Q: Can I change the 5 attempts?**  
A: Yes! Set `LOGIN_RATE_LIMIT_PER_MINUTE` in `.env` and restart.

**Q: What about users behind proxy?**  
A: Handles X-Forwarded-For and X-Real-IP headers automatically.

**Q: Why Redis instead of database?**  
A: Redis is faster (~1ms), already configured, auto-expires old data.

**Q: Can I bypass rate limiting?**  
A: No - security feature. But can increase `LOGIN_RATE_LIMIT_PER_MINUTE`.

**Q: Will this slow down login?**  
A: No - Redis operation is ~1-2ms, negligible impact.

**Q: How long does rate limit last?**  
A: 60 seconds (default). Can change with `LOGIN_RATE_LIMIT_WINDOW_SECONDS`.

---

## Support Resources

📖 **Full Technical Guide**: `RATE_LIMITING_IMPLEMENTATION.md`  
🧪 **Test Scenarios**: `RATE_LIMITING_TEST_SCENARIOS.md`  
📋 **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`  

---

## Next Steps

1. **Verify**: Test with curl examples above
2. **Monitor**: Watch logs for first 24 hours
3. **Adjust**: Change limits if needed based on usage
4. **Document**: Share with support/QA team
5. **Report**: Flag any issues immediately

---

## Examples

### Example 1: Normal User Flow
```
User 1 (IP: 203.0.113.10):
- Tries login 3 times with wrong password
- Tries again with correct password
- Gets access token
- Counter resets to 0
- ✅ Success
```

### Example 2: Attacker Scenario
```
Attacker (IP: 198.51.100.50):
- Tries login 10 times with random passwords
- Attempts 1-5: HTTP 401
- Attempts 6-10: HTTP 429 (rate limited)
- Waits 60 seconds
- Tries again: Counter reset, can try 5 more times
- ✅ Protected
```

### Example 3: Shared Network
```
Users A & B (same IP: 192.0.2.1):
- User A: 2 failed attempts
- User B: 3 failed attempts
- Combined: 5/5 attempts reached
- Both get rate limited (shared IP)
- ✅ Security priority
- Solution: Increase LOGIN_RATE_LIMIT_PER_MINUTE
```

---

## Remember

✅ This is a **security feature**  
✅ Default limits are **production-ready**  
✅ **Zero breaking changes** to existing API  
✅ **Configurable** for your needs  
✅ **Documented** for your team  
✅ **Ready to deploy**  

---

Questions? Check the full documentation files:
- `RATE_LIMITING_IMPLEMENTATION.md` (technical details)
- `RATE_LIMITING_TEST_SCENARIOS.md` (testing guide)
