# SBMS Security & Performance Hardening - Requirements Document

## Introduction

This specification consolidates 8 high-priority issues into a comprehensive security and performance hardening initiative for the Smart Building Management System (SBMS). The system manages building complaints through a secure workflow: Student creation → AI categorization → Admin assignment → Worker resolution → Admin verification → Student feedback → Closure.

The hardening initiative addresses critical gaps in authentication, authorization, input validation, data persistence, and database performance. All changes maintain backward compatibility with existing functionality while significantly improving security posture and system performance.

---

## Glossary

- **System**: The Smart Building Management System (SBMS) FastAPI backend
- **JWT**: JSON Web Token - used for stateless authentication
- **RBAC**: Role-Based Access Control (Admin, Worker, Student roles)
- **Token_Blacklist**: Persistent storage of invalidated JWT tokens
- **Rate_Limiter**: Redis-based mechanism tracking login attempts per IP address
- **File_Validator**: Component verifying MIME types, extensions, and file sizes
- **Verification_Token**: Cryptographically secure token sent via email for account verification
- **N+1_Query**: Performance anti-pattern where loading parent objects triggers one query per child
- **Selectinload**: SQLAlchemy eager loading strategy using separate SELECT statements
- **Joinedload**: SQLAlchemy eager loading strategy using JOIN statements
- **Index**: Database structure optimizing query performance on specific columns
- **Complaint_Workflow**: Process from creation through resolution: Create → Categorize → Assign → Resolve → Verify → Feedback → Close
- **Email_Verification**: Process requiring users to confirm email ownership before account activation
- **IP_Address**: Unique identifier for login rate limiting (from client connection)
- **Retry_After**: HTTP header indicating when client should retry after rate limit

---

## Requirements

### Requirement 1: Secure Building Retrieval Endpoint

**User Story:** As an Admin/Worker/Student, I want to retrieve building data securely, so that unauthorized users cannot access building information.

#### Acceptance Criteria

1. WHEN a request is made to GET /buildings, THE System SHALL verify the user is authenticated with a valid JWT token
2. WHEN a request is made to GET /buildings by a Student, THE System SHALL return only buildings associated with that student's campus
3. WHEN a request is made to GET /buildings by a Worker, THE System SHALL return only buildings assigned to that worker
4. WHEN a request is made to GET /buildings by an Admin, THE System SHALL return all buildings in the system
5. IF a request contains an invalid or expired JWT token, THEN THE System SHALL return HTTP 401 (Unauthorized)
6. IF a request contains no JWT token, THEN THE System SHALL return HTTP 401 (Unauthorized)
7. IF a request contains a valid JWT but the user lacks permissions, THEN THE System SHALL return HTTP 403 (Forbidden)
8. THE System SHALL include JWT authentication in the OpenAPI documentation for GET /buildings

---

### Requirement 2: Login Rate Limiting

**User Story:** As a security administrator, I want login attempts to be rate-limited, so that brute-force attacks are mitigated.

#### Acceptance Criteria

1. WHEN a user attempts to login via POST /auth/login, THE Rate_Limiter SHALL track the request count by client IP address
2. WHEN a single IP address exceeds 5 login attempts within 60 seconds, THE System SHALL reject the next attempt with HTTP 429 (Too Many Requests)
3. WHEN a HTTP 429 response is sent, THE System SHALL include the Retry-After header indicating seconds until retry is permitted
4. WHEN a login attempt succeeds, THE Rate_Limiter SHALL reset the attempt counter for that IP address to zero
5. WHEN a login attempt fails, THE Rate_Limiter SHALL increment the attempt counter for that IP address by one
6. THE System SHALL store rate limit state in Redis with automatic expiration (default: 60 seconds per window)
7. THE Rate_Limiter SHALL use the X-Forwarded-For header for client IP detection when available (proxy awareness)
8. WHERE the rate limit window duration is configurable, THE System SHALL accept MAX_LOGIN_ATTEMPTS and LOGIN_RATE_LIMIT_WINDOW_SECONDS environment variables

---

### Requirement 3: File Upload Validation

**User Story:** As a security officer, I want uploaded files to be strictly validated, so that malicious files cannot be stored in the system.

#### Acceptance Criteria

1. WHEN a file is uploaded to the System, THE File_Validator SHALL verify the file extension is in the whitelist: [.jpg, .jpeg, .png, .webp]
2. WHEN a file is uploaded to the System, THE File_Validator SHALL verify the MIME type is in the whitelist: [image/jpeg, image/png, image/webp]
3. WHEN a file is uploaded to the System, THE File_Validator SHALL verify the file size does not exceed 10 MB (10485760 bytes)
4. IF a file extension is not in the whitelist, THEN THE System SHALL reject the upload with HTTP 400 (Bad Request) and descriptive error message
5. IF a MIME type does not match the extension or is not in the whitelist, THEN THE System SHALL reject the upload with HTTP 400 (Bad Request)
6. IF file size exceeds 10 MB, THEN THE System SHALL reject the upload with HTTP 413 (Payload Too Large)
7. WHEN a file is validated successfully, THE System SHALL generate a secure filename using UUID v4 and preserve original extension
8. THE System SHALL prevent path traversal attacks by stripping directory separators from filenames
9. THE System SHALL reject the following file types explicitly: .exe, .bat, .cmd, .com, .scr, .svg, .pdf, .zip, .rar, .7z, .tar, .gz and any executable script extensions
10. WHERE file size limit is configurable, THE System SHALL accept MAX_UPLOAD_SIZE_MB environment variable

---

### Requirement 4: Persistent Token Blacklist

**User Story:** As an administrator, I want logged-out tokens to remain invalidated across system restarts, so that session management is reliable and secure.

#### Acceptance Criteria

1. WHEN a user logs out via POST /auth/logout, THE System SHALL add the user's JWT token to the Token_Blacklist in PostgreSQL
2. WHEN a Token_Blacklist entry is created, THE System SHALL store: token hash, user_id, expiration_time, creation_timestamp, and revocation_reason
3. WHEN a Token_Blacklist entry is created, THE System SHALL set automatic deletion 24 hours after the token's original expiration time
4. BEFORE processing any JWT-authenticated request, THE Middleware SHALL query the Token_Blacklist to verify the token is not revoked
5. IF a token exists in the Token_Blacklist, THEN THE System SHALL reject the request with HTTP 401 (Unauthorized)
6. WHEN a token's expiration time passes, THE System SHALL automatically delete the entry from the Token_Blacklist via database cleanup job (runs daily at 02:00 UTC)
7. THE Token_Blacklist table SHALL include a database index on token_hash for O(1) lookup performance
8. THE Token_Blacklist SHALL maintain a Redis cache layer for frequently-checked tokens with 5-minute TTL (10-second refresh on miss)
9. WHERE token blacklist behavior is configurable, THE System SHALL accept TOKEN_BLACKLIST_CLEANUP_HOUR and TOKEN_BLACKLIST_CACHE_TTL_SECONDS environment variables

---

### Requirement 5: Email Verification on Registration

**User Story:** As a system administrator, I want new user accounts to require email verification, so that invalid email addresses are prevented and account takeover is mitigated.

#### Acceptance Criteria

1. WHEN a user registers via POST /auth/register, THE System SHALL generate a cryptographically secure Verification_Token (32 bytes, URL-safe)
2. WHEN a Verification_Token is generated, THE System SHALL hash it using SHA-256 and store only the hash in the database
3. WHEN a user registration completes, THE System SHALL send an email containing a verification link with the unhashed token
4. WHEN a user registration completes, THE System SHALL set the user's email_verified flag to false
5. IF a user attempts to login with email_verified=false, THEN THE System SHALL reject the login with HTTP 403 (Forbidden) and error message: "Email not verified"
6. WHEN a user accesses the verification link with valid token, THE System SHALL verify the token against stored hash using constant-time comparison
7. WHEN a verification token is validated successfully, THE System SHALL set email_verified=true and delete the verification token record
8. WHEN a verification token is created, THE System SHALL set expiration to 24 hours from creation
9. IF a verification token has expired, THEN THE System SHALL reject verification with HTTP 400 (Bad Request) and error message: "Token expired"
10. WHEN a user requests token resend via POST /auth/resend-verification-email, THE System SHALL generate a new Verification_Token (invalidating previous ones)
11. WHEN a user requests token resend, THE Rate_Limiter SHALL permit maximum 3 resend requests per 60 minutes per email address
12. WHERE email verification is configurable, THE System SHALL accept EMAIL_VERIFICATION_ENABLED, VERIFICATION_TOKEN_EXPIRY_HOURS, and RESEND_EMAIL_RATE_LIMIT environment variables

---

### Requirement 6: Database Performance - Query Indexes

**User Story:** As a database administrator, I want critical queries to use indexes, so that complaint listing and filtering operations perform efficiently.

#### Acceptance Criteria

1. THE System SHALL create a database index on complaints.status column for efficient filtering by complaint status
2. THE System SHALL create a database index on complaints.assigned_to column for finding complaints by assigned worker
3. THE System SHALL create a database index on complaints.created_at column for efficient temporal filtering and sorting
4. THE System SHALL create a database index on ticket_logs.complaint_id column for quick log lookup by complaint
5. THE System SHALL create a database index on notifications.user_id column for efficient notification retrieval per user
6. THE System SHALL create a database index on notifications.is_read column for finding unread notification counts
7. WHEN creating indexes, THE System SHALL verify no duplicate indexes exist on same columns in same order
8. THE System SHALL create all indexes via Alembic migration (new migration file following existing naming convention)
9. WHEN the migration is applied, THE System SHALL log index creation completion with execution time
10. WHERE indexes are configurable, THE System SHALL document index strategy in migration file comments

---

### Requirement 7: N+1 Query Optimization

**User Story:** As a performance engineer, I want complaint queries to load related data efficiently, so that no additional queries are triggered during result iteration.

#### Acceptance Criteria

1. WHEN a complaint is retrieved via GET /complaints/{id}, THE System SHALL eagerly load: assigned_worker, created_by_student, and notifications using selectinload() or joinedload()
2. WHEN complaint list is retrieved via GET /complaints, THE System SHALL eagerly load assigned_worker relationship for all returned complaints in a single query
3. WHEN complaint list is retrieved via GET /complaints, THE System SHALL eagerly load notifications relationship for all returned complaints in a single query
4. WHEN iterating over complaint results, THE System SHALL not trigger additional SELECT queries for related objects
5. THE System SHALL use SQLAlchemy selectinload() for one-to-many relationships (Complaint → Notifications, Complaint → TicketLogs)
6. THE System SHALL use SQLAlchemy joinedload() for many-to-one relationships (Complaint → Worker, Complaint → Student)
7. WHEN notification list is retrieved via GET /notifications, THE System SHALL eagerly load the associated complaint object
8. THE System SHALL audit all repository methods in complaint_service.py and notification_service.py to verify eager loading strategy
9. THE System SHALL add comments in code documenting which relationships are eagerly loaded and why
10. WHERE query optimization strategy is documented, THE System SHALL maintain a PERFORMANCE_NOTES section in relevant service files

---

### Requirement 8: General Security Hardening

**User Story:** As a security architect, I want comprehensive security hardening across all endpoints, so that the system is resilient against common attack vectors.

#### Acceptance Criteria

1. WHEN user input is received from any endpoint, THE System SHALL validate all input according to schema definition using Pydantic validators
2. WHEN an endpoint processes database queries, THE System SHALL use parameterized queries via SQLAlchemy ORM (no string interpolation)
3. IF an unhandled exception occurs in any route, THEN THE System SHALL return a generic HTTP 500 response without exposing stack traces or internal details
4. WHEN exceptions are caught in routes, THE System SHALL log full exception details (including stack traces) to backend logging system, not to client
5. IF a user requests a resource they do not own, THEN THE System SHALL verify ownership before returning data (no information disclosure)
6. WHEN a resource endpoint requires authorization, THE System SHALL verify permissions are checked before data retrieval (defense in depth)
7. WHEN user passwords are created/updated, THE System SHALL enforce minimum requirements: 12 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character
8. WHEN password validation fails, THE System SHALL return generic message: "Password does not meet requirements" (no hint which requirement failed)
9. THE System SHALL implement CORS policy restricting cross-origin requests to configured domains only (configurable via CORS_ALLOWED_ORIGINS environment variable)
10. THE System SHALL verify CORS policy allows only specified HTTP methods (GET, POST, PUT, DELETE) per endpoint
11. WHEN sensitive data is logged (usernames, IDs), THE System SHALL never log authentication tokens, passwords, or personal email addresses
12. THE System SHALL sanitize all user-provided strings to prevent XSS attacks when data is returned in JSON responses (JSON encoding is sufficient)
13. WHERE security hardening configuration is needed, THE System SHALL accept CORS_ALLOWED_ORIGINS, PASSWORD_MIN_LENGTH, and PASSWORD_COMPLEXITY_REQUIRED environment variables

---

## Dependencies & Sequencing

The following dependencies exist between requirements and must be addressed in this order:

1. **Phase 1 (Foundation - Must complete first)**
   - Req 4: Persistent Token Blacklist (prerequisite for logout security)
   - Req 1: Secure Building Retrieval (foundational RBAC)

2. **Phase 2 (Authentication hardening)**
   - Req 2: Login Rate Limiting (depends on Req 4 for logout state)
   - Req 5: Email Verification (depends on Req 1 for auth, Req 4 for logout)

3. **Phase 3 (Input & file security)**
   - Req 3: File Upload Validation (independent)
   - Req 8: General Security Hardening (covers cross-cutting concerns)

4. **Phase 4 (Performance)**
   - Req 6: Database Indexes (independent)
   - Req 7: N+1 Query Optimization (independent)

---

## Constraints

- **Backward Compatibility**: All changes must maintain backward compatibility with existing API contracts. Existing clients should not break.
- **No Breaking Changes**: Database schema changes must be additive; no columns, tables, or indexes may be removed.
- **Environment Configuration**: All configurable values must support environment variables with sensible defaults.
- **Logging & Audit**: All security-related events (login attempts, token revocation, file rejections) must be logged.
- **Performance**: No query should execute more than once per request after optimization (Req 7).
- **Test Coverage**: All new functionality must include unit and integration tests with >90% code coverage.

---

## Implementation Notes

### Configuration via Environment Variables

All requirements include environment variable support with defaults:

| Variable | Requirement | Default | Type |
|----------|-------------|---------|------|
| MAX_LOGIN_ATTEMPTS | Req 2 | 5 | int |
| LOGIN_RATE_LIMIT_WINDOW_SECONDS | Req 2 | 60 | int |
| MAX_UPLOAD_SIZE_MB | Req 3 | 10 | int |
| TOKEN_BLACKLIST_CLEANUP_HOUR | Req 4 | 2 | int (UTC) |
| TOKEN_BLACKLIST_CACHE_TTL_SECONDS | Req 4 | 300 | int |
| EMAIL_VERIFICATION_ENABLED | Req 5 | true | bool |
| VERIFICATION_TOKEN_EXPIRY_HOURS | Req 5 | 24 | int |
| RESEND_EMAIL_RATE_LIMIT | Req 5 | 3 | int |
| CORS_ALLOWED_ORIGINS | Req 8 | localhost:3000 | string (comma-separated) |
| PASSWORD_MIN_LENGTH | Req 8 | 12 | int |
| PASSWORD_COMPLEXITY_REQUIRED | Req 8 | true | bool |

### Logging Requirements

All requirements must generate audit logs:

- **Req 1**: Access attempts to /buildings (success/failure with user/role)
- **Req 2**: Rate limit violations with IP address and timestamp
- **Req 3**: File upload rejections with filename, MIME type, size
- **Req 4**: Token revocation events with user_id and reason
- **Req 5**: Email verification: token generation, verification success/failure
- **Req 8**: Failed security validation attempts with endpoint and reason

### Database Migrations

- **Req 4**: New table `token_blacklist` with columns: id, token_hash (indexed, unique), user_id (FK), expires_at, created_at, revocation_reason
- **Req 5**: Add columns to `user` table: email_verified (bool, default false), verification_token_hash (nullable), verification_token_expires_at (nullable)
- **Req 6**: Create indexes on complaints, ticket_logs, notifications tables (see Req 6 acceptance criteria)

---

## Acceptance Criteria Testing Strategy

### Property-Based Testing Recommendations

- **Req 1**: RBAC permissions should be idempotent (same role always gets same results)
- **Req 2**: Rate limit counter resets correctly after window expiration
- **Req 3**: All valid images pass validation; all invalid files fail consistently
- **Req 4**: Token blacklist queries return consistent results
- **Req 7**: Query count should never exceed N+1 for any dataset size

### Integration Testing Recommendations

- **Req 1**: Test with each role accessing buildings (Student, Worker, Admin)
- **Req 2**: Verify rate limit behavior across multiple clients
- **Req 5**: Complete email verification flow end-to-end
- **Req 8**: CORS policy enforcement with cross-origin requests

---
