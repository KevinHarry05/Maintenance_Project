# Implementation Plan: SBMS Security & Performance Hardening

## Overview

This implementation plan converts the SBMS Security & Performance Hardening design into discrete, actionable coding tasks. The design uses Python (FastAPI backend) for implementation. Tasks are organized into logical phases aligned with dependency requirements and cover all 8 security and performance initiatives: RBAC for building retrieval, login rate limiting, file upload validation, persistent token blacklist, email verification, database indexes, N+1 query optimization, and comprehensive security hardening.

## Phase 1: Foundation - Database & Models (RBAC & Token Blacklist)

### Database Migrations & Schema

- [x] 1.1 Create Alembic migration for token_blacklist table
  - Create new migration file following naming convention: `<timestamp>_add_token_blacklist_table.py`
  - Define token_blacklist table with columns: id, token_hash (unique, indexed), user_id (FK), expires_at, created_at, revocation_reason
  - Create indexes: idx_token_hash, idx_user_id, idx_expires_at
  - _Requirements: 4.2, 4.7_

- [x] 1.2 Create Alembic migration to extend User model with email verification fields
  - Add columns to users table: email_verified (BOOLEAN, DEFAULT FALSE), created_at timestamp if missing
  - _Requirements: 5.4_

- [x] 1.3 Create Alembic migration for email_verification_tokens table
  - Create email_verification_tokens table with columns: id, user_id (unique FK), token_hash (unique, indexed), expires_at, created_at
  - Create indexes: idx_token_hash, idx_expires_at
  - _Requirements: 5.2, 5.8_

- [x] 1.4 Create Alembic migration for complaint query performance indexes
  - Create indexes: idx_complaints_status, idx_complaints_assigned_to, idx_complaints_created_at
  - Create composite index: idx_complaints_status_created on (status, created_at DESC)
  - _Requirements: 6.1, 6.2, 6.3, 6.8_

- [x] 1.5 Create Alembic migration for supporting table indexes
  - Create indexes: idx_ticket_logs_complaint_id, idx_notifications_user_id
  - Create partial index: idx_notifications_is_read on (is_read) WHERE is_read = false
  - _Requirements: 6.4, 6.5, 6.6, 6.8_

- [ ]* 1.6 Write unit tests for Alembic migrations
  - Test each migration applies without errors
  - Test migrations can be downgraded cleanly
  - Verify indexes are created correctly
  - _Requirements: 6.8_

### SQLAlchemy Models

- [x] 1.7 Create TokenBlacklist model in app/models/
  - Create file: app/models/token_blacklist.py
  - Define TokenBlacklist class with all fields from design: token_hash, user_id (FK), expires_at, created_at, revocation_reason
  - Implement is_expired() method for token expiration checks
  - Add relationship to User model
  - _Requirements: 4.2_

- [x] 1.8 Create EmailVerificationToken model in app/models/
  - Create file: app/models/email_verification_token.py
  - Define EmailVerificationToken class with fields: user_id (unique FK), token_hash (unique), expires_at, created_at
  - Implement is_expired() method
  - Add relationship to User model
  - _Requirements: 5.2_

- [x] 1.9 Update User model with email verification fields
  - Add email_verified field (Boolean, default False) to User model
  - Verify backward compatibility (existing users treated as verified via migration)
  - Update User imports and relationships to include email verification token
  - _Requirements: 5.4_

- [x] 1.10 Update Complaint model with eager loading relationships
  - Configure relationships with lazy="select" for: created_by, assigned_worker, notifications, ticket_logs
  - Add comments documenting eager loading strategy for each relationship
  - _Requirements: 7.1_

- [ ]* 1.11 Write unit tests for all model definitions
  - Test model instantiation and validation
  - Test relationship definitions
  - Test is_expired() methods
  - _Requirements: 4.2, 5.2, 7.1_


## Phase 2: Token Blacklist & RBAC Implementation

### Token Blacklist Repository & Services

- [x] 2.1 Create TokenBlacklist repository with database operations
  - Create file: app/services/token_blacklist_repository.py
  - Implement methods: add_to_blacklist(token_hash, user_id, expires_at, reason), is_blacklisted(token_hash), cleanup_expired_tokens()
  - Implement O(1) lookup using token_hash index
  - _Requirements: 4.1, 4.3, 4.7_

- [x] 2.2 Create token blacklist Redis cache layer
  - Create file: app/services/token_blacklist_cache.py
  - Implement Redis cache with 5-minute TTL using prefix "blacklist:{token_hash}"
  - Implement get(), set(), delete() methods
  - Use redis.setex() for automatic expiration
  - _Requirements: 4.8_

- [-] 2.3 Implement token revocation in auth service
  - Update app/routes/auth.py with POST /auth/logout endpoint
  - Extract JWT token from Authorization header
  - Hash token using SHA-256
  - Call token_blacklist_repository.add_to_blacklist() with token hash, user_id, expiration, and reason="user_logout"
  - Cache result in Redis cache layer
  - Return success response with 200 OK
  - Log token revocation event with user_id and timestamp
  - _Requirements: 4.1, 4.3_

- [-] 2.4 Create token blacklist middleware for all protected endpoints
  - Create file: app/core/token_blacklist_middleware.py
  - Extract JWT token from Authorization header in all authenticated requests
  - Hash token using SHA-256
  - Check Redis cache first (10-second refresh on miss per design)
  - If not cached, query PostgreSQL TokenBlacklist table
  - If found in blacklist, return HTTP 401 with message "Token has been revoked"
  - Cache result in Redis with 5-minute TTL if found
  - Continue to next middleware if token not blacklisted
  - _Requirements: 4.4, 4.5_

- [~] 2.5 Create daily token blacklist cleanup scheduled task
  - Create file: app/tasks/token_blacklist_cleanup.py
  - Implement scheduled task that runs daily at 02:00 UTC (configurable via TOKEN_BLACKLIST_CLEANUP_HOUR env var)
  - Query TokenBlacklist table for entries where expires_at < current_time
  - Delete expired entries from database
  - Log cleanup event with count of deleted entries
  - _Requirements: 4.6_

- [ ]* 2.6 Write unit tests for token blacklist services
  - Test add_to_blacklist() creates entries correctly
  - Test is_blacklisted() returns true for blacklisted tokens
  - Test cache hit and miss scenarios
  - Test cleanup task removes expired tokens
  - Test Redis cache expiration
  - _Requirements: 4.1, 4.8_

- [ ]* 2.7 Write integration tests for logout flow
  - Test complete logout flow: login → get token → logout → verify token rejected
  - Test token is immediately unavailable after logout
  - Test cache and database consistency
  - _Requirements: 4.1, 4.3, 4.4_

### RBAC for Building Retrieval

- [-] 2.8 Implement RBAC permission decorator
  - Create file: app/core/rbac_decorator.py
  - Implement decorator @require_role(roles=['admin', 'worker', 'student'])
  - Extract user role from JWT token in request
  - Check if role is in allowed list
  - Return HTTP 403 Forbidden if role not authorized
  - Continue to endpoint handler if authorized
  - _Requirements: 1.7, 1.8_

- [ ] 2.9 Update GET /buildings endpoint with RBAC
  - Modify app/routes/building.py GET /buildings endpoint
  - Add JWT authentication requirement (verify token not in blacklist)
  - Add role-based filtering:
    - Admin role: return all buildings
    - Worker role: return only buildings assigned to worker (filter by building.assigned_workers or similar relationship)
    - Student role: return only buildings on student's campus (filter by student.campus == building.campus)
  - Return 401 Unauthorized if no valid JWT token
  - Return 403 Forbidden if user role lacks permission
  - Log access attempts with user role and result (success/failure)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [~] 2.10 Update OpenAPI documentation for GET /buildings
  - Add security schema to endpoint: security: [bearer: []]
  - Document 401 Unauthorized response
  - Document 403 Forbidden response
  - Add role-based filtering description
  - _Requirements: 1.8_

- [ ]* 2.11 Write property tests for RBAC
  - **Property 1: Role-based idempotence** - Same role always retrieves same building set for identical filters
  - **Validates: Requirements 1.2, 1.3, 1.4**

- [ ]* 2.12 Write integration tests for building retrieval with RBAC
  - Test Admin role retrieves all buildings
  - Test Worker role retrieves only assigned buildings
  - Test Student role retrieves only campus buildings
  - Test unauthenticated request returns 401
  - Test invalid role returns 403
  - _Requirements: 1.1, 1.2, 1.3, 1.4_


## Phase 3: Authentication Hardening (Rate Limiting & Email Verification)

### Login Rate Limiting

- [~] 3.1 Enhance login rate limiter with Redis backend
  - Update app/core/login_rate_limiter.py to use Redis as primary backend
  - Extract client IP from request using X-Forwarded-For header (proxy awareness) or remote address
  - Track login attempt count per IP address in Redis key format: "login_attempts:{ip_address}"
  - Use Redis INCR command to increment counter on each failed attempt
  - Use Redis SETEX to set TTL = LOGIN_RATE_LIMIT_WINDOW_SECONDS (default 60 seconds, configurable)
  - On successful login, delete the counter key to reset attempts
  - Store current attempt count and timestamp for rate limit window
  - _Requirements: 2.1, 2.2, 2.6, 2.7, 2.8_

- [~] 3.2 Implement HTTP 429 response with Retry-After header
  - Update POST /auth/login endpoint rate limit check
  - When attempt count exceeds MAX_LOGIN_ATTEMPTS (default 5, configurable):
    - Calculate seconds remaining in current window
    - Return HTTP 429 Too Many Requests response
    - Include Retry-After header with value = seconds_remaining
    - Include error message in JSON response
  - _Requirements: 2.2, 2.3_

- [~] 3.3 Log rate limit violations
  - Add logging to login_rate_limiter for each violation
  - Log format: IP address, timestamp, current attempt count, window duration
  - Use structured logging with severity level WARNING
  - Prevent password/email from being logged
  - _Requirements: 2.6_

- [ ]* 3.4 Write unit tests for rate limiter
  - Test counter increments on failed login
  - Test counter resets on successful login
  - Test 429 response after exceeding limit
  - Test Retry-After header is present and correct
  - Test X-Forwarded-For proxy detection
  - Test rate limit window expiration
  - _Requirements: 2.1, 2.2, 2.3, 2.6_

- [ ]* 3.5 Write integration tests for login rate limiting
  - Test complete rate limit flow: 5 failed attempts → 429 response
  - Test rate limit applies per IP address
  - Test successful login resets counter
  - Test rate limit window resets after timeout
  - _Requirements: 2.1, 2.2, 2.3_

### Email Verification

- [~] 3.6 Implement secure token generation and hashing
  - Create file: app/services/email_verification_service.py
  - Implement generate_verification_token(): generate 32 bytes of cryptographically secure random data using secrets.token_urlsafe()
  - Implement hash_verification_token(): hash token using SHA-256, return hex digest
  - Implement verify_token_hash(): use constant-time comparison (hmac.compare_digest) to prevent timing attacks
  - _Requirements: 5.1, 5.2, 5.6_

- [~] 3.7 Extend POST /auth/register with email verification flow
  - Update app/routes/auth.py POST /auth/register endpoint
  - After user creation (with email_verified=false):
    - Generate verification token using email_verification_service.generate_verification_token()
    - Hash token and store hash in email_verification_tokens table with user_id, expires_at (24 hours)
    - Send verification email with token and link format: https://{domain}/auth/verify?token={raw_token}
    - Return 201 Created response with user_id, email, email_verified=false
  - Log email verification token generation
  - _Requirements: 5.1, 5.2, 5.3_

- [~] 3.8 Implement email verification endpoint GET /auth/verify
  - Create GET /auth/verify endpoint in app/routes/auth.py
  - Accept token query parameter (raw, unhashed token)
  - Hash token using email_verification_service.hash_verification_token()
  - Query email_verification_tokens table for matching token_hash
  - If not found, return HTTP 400 "Invalid or malformed verification token"
  - If found, check expiration: if expires_at < now(), delete token and return HTTP 400 "Verification token has expired"
  - If valid and not expired:
    - Set user.email_verified = true
    - Delete verification token record
    - Return HTTP 200 with message "Email verified successfully"
  - Log verification success/failure with user_id
  - _Requirements: 5.6, 5.7, 5.8, 5.9_

- [~] 3.9 Implement POST /auth/resend-verification-email endpoint
  - Create new endpoint in app/routes/auth.py
  - Accept email address in request body
  - Query user by email; if not found, return generic response (no user enumeration)
  - Check rate limit: max 3 requests per 60 minutes per email (configurable RESEND_EMAIL_RATE_LIMIT, default 3)
  - If rate limited, return HTTP 429 with appropriate message
  - Generate new verification token (invalidating previous ones by UNIQUE constraint on user_id)
  - Send new verification email
  - Return HTTP 200 with message "Verification email resent"
  - Log resend event
  - _Requirements: 5.10, 5.11_

- [~] 3.10 Implement login check for email_verified flag
  - Update POST /auth/login endpoint in app/routes/auth.py
  - After credentials validation, before returning JWT:
    - Check user.email_verified flag
    - If false, return HTTP 403 Forbidden with message "Email not verified. Please verify your email to login."
  - _Requirements: 5.5_

- [~] 3.11 Create email template for verification
  - Create file: app/templates/verification_email.html
  - Design professional email template with:
    - Welcome message with user name
    - Verification link (clickable)
    - Token expiration time (24 hours)
    - Support contact information
  - Create alternate plain text version: app/templates/verification_email.txt
  - _Requirements: 5.3_

- [ ]* 3.12 Write unit tests for email verification service
  - Test token generation produces valid URL-safe strings
  - Test token hashing is deterministic
  - Test verify_token_hash with correct and incorrect tokens
  - Test constant-time comparison (timing attack resistance)
  - Test token expiration checks
  - _Requirements: 5.1, 5.2, 5.6_

- [ ]* 3.13 Write integration tests for email verification flow
  - Test complete registration → email sent → verification → login flow
  - Test expired token rejection
  - Test invalid token rejection
  - Test resend rate limiting
  - Test unauthenticated login attempts rejected for unverified emails
  - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.8, 5.10_

- [~] 3.14 Checkpoint - Ensure authentication phase complete
  - Ensure all authentication tests pass
  - Verify rate limiting is working correctly
  - Verify email verification flow is complete
  - Ask the user if questions arise.


## Phase 4: File Upload Security

### File Validation Service

- [~] 4.1 Create file validator service with comprehensive checks
  - Create file: app/services/file_validator.py
  - Implement FileValidator class with static methods:
    - validate_filename(filename): Check for path traversal (../, directory separators, forbidden chars)
    - validate_extension(filename): Check extension against whitelist (.jpg, .jpeg, .png, .webp)
    - validate_mime_type(mime_type): Check MIME type against whitelist (image/jpeg, image/png, image/webp)
    - validate_file_size(file_size_bytes): Check against MAX_UPLOAD_SIZE_MB (default 10 MB, configurable)
    - validate_magic_numbers(file_content): Verify file signature matches extension
  - Raise custom exceptions: InvalidExtensionException, InvalidMimeTypeException, PathTraversalException
  - Log all validation failures with file details (excluding sensitive paths)
  - _Requirements: 3.1, 3.2, 3.3, 3.7, 3.8, 3.9_

- [~] 4.2 Implement secure filename generation
  - Add method to FileValidator: generate_secure_filename(original_filename)
  - Extract extension from original filename
  - Generate UUID v4 and convert to string
  - Combine: {uuid}.{extension}
  - Verify filename contains no directory separators or path traversal attempts
  - Return sanitized filename safe for file system storage
  - _Requirements: 3.7_

- [~] 4.3 Update file upload endpoint with validation
  - Modify app/routes/complaints.py (or appropriate upload endpoint) POST /complaints/{complaint_id}/upload
  - Add authentication requirement (JWT token)
  - Verify request user owns complaint (or has permission to upload)
  - Extract uploaded file from multipart/form-data
  - Validate filename: call file_validator.validate_filename()
  - Validate extension: call file_validator.validate_extension()
  - Validate MIME type: call file_validator.validate_mime_type()
  - Validate file size: call file_validator.validate_file_size()
  - Validate magic numbers: call file_validator.validate_magic_numbers()
  - If any validation fails, return HTTP 400 (Bad Request) or HTTP 413 (Payload Too Large) with specific error message
  - Generate secure filename: call file_validator.generate_secure_filename()
  - Store file to disk (implementation details depend on current setup)
  - Record metadata in database (if applicable)
  - Return HTTP 200 with file details (file_id, filename, original_filename, size, mime_type, url)
  - Log successful uploads and all rejections
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [~] 4.4 Implement forbidden file type blacklist
  - Extend FileValidator with FORBIDDEN_EXTENSIONS set
  - Add extensions: .exe, .bat, .cmd, .com, .scr, .svg, .pdf, .zip, .rar, .7z, .tar, .gz (+ script extensions)
  - Check filename extension against blacklist in validate_extension()
  - Return specific error: "File extension is not allowed due to security restrictions"
  - Log forbidden extension attempts as WARNING level
  - _Requirements: 3.9_

- [ ]* 4.5 Write unit tests for file validator
  - Test valid image files pass all validators
  - Test invalid extensions rejected with 400
  - Test invalid MIME types rejected with 400
  - Test oversized files rejected with 413
  - Test path traversal attempts rejected
  - Test magic number validation (file signature checking)
  - Test forbidden extensions rejected
  - Test secure filename generation (UUID format, no traversal chars)
  - _Requirements: 3.1, 3.2, 3.3, 3.7, 3.8, 3.9_

- [ ]* 4.6 Write integration tests for file upload endpoint
  - Test complete upload flow with valid image file
  - Test rejection with invalid extension (.exe, .pdf, .zip)
  - Test rejection with oversized file (>10 MB)
  - Test rejection with mismatched MIME type
  - Test rejection with path traversal filename (../../etc/passwd)
  - Test multiple files uploaded sequentially
  - Test authentication required (401 without token)
  - Test authorization (403 if user doesn't own complaint)
  - _Requirements: 3.1, 3.4, 3.5, 3.6_

## Phase 5: Security Hardening (Input Validation & Error Handling)

### Input Validation & Error Handling

- [~] 5.1 Implement comprehensive input validation using Pydantic schemas
  - Audit all request schemas in app/schemas/
  - Verify each schema uses Pydantic validators
  - Add custom validators where needed using @field_validator
  - Validate email format, string lengths, numeric ranges, enum values
  - For password fields: use PasswordValidator to enforce requirements
  - For file uploads: validate using FileValidator
  - Ensure all user input is validated at schema level
  - _Requirements: 8.1_

- [~] 5.2 Implement secure error handling across all endpoints
  - Create file: app/core/error_handler.py
  - Implement exception handlers for all route exception types
  - For unhandled exceptions:
    - Log full exception details (stack trace, user_id, endpoint, request body) to logger
    - Return generic HTTP 500 response to client: "Internal server error"
    - Include request_id for client to reference in support requests
  - For validation errors (422 Unprocessable Entity):
    - Return validation errors in response (safe to expose)
    - Never expose schema or code internals
  - For authentication errors (401):
    - Return generic message: "Authorization credentials are missing or invalid"
    - Do not indicate whether email exists or password is wrong
  - For authorization errors (403):
    - Return generic message: "User does not have permission to access resource"
  - _Requirements: 8.3, 8.4_

- [~] 5.3 Implement ownership verification for resource access
  - Create decorator @verify_ownership(resource_type)
  - Decorator extracts user_id from JWT token
  - Before endpoint handler executes:
    - Query resource by ID
    - Check user_id matches resource.user_id or user in authorized_users list
    - Return 403 Forbidden if not owner/authorized
    - Continue to handler if authorized
  - Apply decorator to all endpoints accessing user-owned resources
  - Examples: GET /complaints/{id}, DELETE /complaints/{id}, POST /complaints/{id}/upload
  - _Requirements: 8.5_

- [~] 5.4 Implement permission checks before data retrieval
  - Add @require_permission(permission_name) decorator
  - Check user role has permission before database query
  - Defense in depth: verify both at decorator level and in service layer
  - Return 403 Forbidden if permission denied
  - Log authorization failures
  - _Requirements: 8.6_

### Password Security

- [~] 5.5 Implement password validation service
  - Create file: app/services/password_validator.py
  - Implement PasswordValidator class (or extend existing):
    - validate(password): Check minimum 12 characters, 1 uppercase, 1 lowercase, 1 digit, 1 special char
    - Return (is_valid: bool, message: str)
    - If invalid, return generic message: "Password does not meet requirements" (no hint which requirement failed)
    - hash_password(password): Use bcrypt with appropriate cost factor
    - verify_password(plain, hashed): Compare plain password against hash
  - _Requirements: 8.7, 8.8_

- [~] 5.6 Update user registration and password change endpoints
  - Update POST /auth/register endpoint:
    - Call PasswordValidator.validate(password) before user creation
    - Return 400 with generic error message if validation fails
  - Update password change endpoint (if exists):
    - Call PasswordValidator.validate(password)
    - Use PasswordValidator.hash_password() for storage
    - Use PasswordValidator.verify_password() for verification
  - _Requirements: 8.7_

### CORS & Security Headers

- [~] 5.7 Implement CORS policy with configuration
  - Update app/main.py FastAPI configuration
  - Use FastAPI CORSMiddleware
  - Read CORS_ALLOWED_ORIGINS from environment (default: localhost:3000)
  - Configure allowed_origins as comma-separated list parsed into array
  - Configure allowed_methods: [GET, POST, PUT, DELETE, OPTIONS]
  - Configure allowed_headers: [*] or specific headers (Content-Type, Authorization)
  - Verify CORS policy is restrictive (not allow_credentials=True with allow_origins=[*])
  - _Requirements: 8.9, 8.10_

- [~] 5.8 Add security headers to all responses
  - Create middleware: app/core/security_headers_middleware.py
  - Add headers to all responses:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains (if HTTPS)
  - Do not expose Server header or version information
  - _Requirements: 8.12_

### Sensitive Data Logging

- [~] 5.9 Implement secure logging for sensitive operations
  - Update app/core/logger.py (or create if needed)
  - When logging user-related events:
    - Never log authentication tokens (JWT, session tokens)
    - Never log passwords or password hashes
    - Never log personal email addresses (use user_id or anonymized reference instead)
    - OK to log: user_id, username, role, action, timestamp, status
    - OK to log: IP address, endpoint, HTTP method, status code
  - Implement log filtering to redact sensitive patterns
  - Log to file and/or structured logger (not stdout in production)
  - _Requirements: 8.11_

- [ ]* 5.10 Write unit tests for error handling
  - Test generic error message returned for unhandled exceptions
  - Test error details logged internally (check log output)
  - Test validation errors returned correctly
  - Test ownership verification denies unauthorized users
  - Test permission checks work correctly
  - _Requirements: 8.3, 8.4, 8.5, 8.6_

- [ ]* 5.11 Write unit tests for password validation
  - Test valid password accepted
  - Test too short password rejected
  - Test missing uppercase rejected
  - Test missing lowercase rejected
  - Test missing digit rejected
  - Test missing special character rejected
  - Test generic error message (no hint which requirement failed)
  - Test password hashing and verification
  - _Requirements: 8.7, 8.8_

- [ ]* 5.12 Write integration tests for CORS policy
  - Test allowed origin succeeds (200)
  - Test disallowed origin rejected (CORS error)
  - Test preflight OPTIONS requests
  - Test disallowed method rejected (405)
  - _Requirements: 8.9, 8.10_

- [ ]* 5.13 Write integration tests for security headers
  - Test X-Content-Type-Options header present
  - Test X-Frame-Options header present
  - Test X-XSS-Protection header present
  - Test no sensitive information in response headers
  - _Requirements: 8.12_


## Phase 6: Performance Optimization (N+1 Queries & Eager Loading)

### Eager Loading Strategy Implementation

- [~] 6.1 Audit complaint_service.py for N+1 queries
  - Review app/services/complaint_service.py
  - Identify all query methods that retrieve complaints
  - For each method, trace relationships being accessed:
    - created_by (User relationship)
    - assigned_worker (User relationship)
    - notifications (Notification collection)
    - ticket_logs (TicketLog collection)
  - Document current loading strategy (lazy vs eager)
  - Create audit document: PERFORMANCE_NOTES.md section in complaint_service.py
  - _Requirements: 7.8, 7.9_

- [~] 6.2 Implement eager loading for single complaint retrieval
  - Update method: get_complaint_by_id(complaint_id) in complaint_service.py
  - Add eager loading using SQLAlchemy:
    - Use selectinload() for one-to-many relationships: notifications, ticket_logs
    - Use joinedload() for many-to-one relationships: created_by, assigned_worker
  - Example: query = session.query(Complaint).filter(...).options(selectinload('notifications'), joinedload('assigned_worker'))
  - Add inline comment explaining eager loading strategy
  - Verify method returns single Complaint with all relationships loaded
  - _Requirements: 7.1, 7.5, 7.6_

- [~] 6.3 Implement eager loading for complaint list retrieval
  - Update method: list_complaints() in complaint_service.py
  - Apply eager loading to complaint collection query:
    - Use selectinload() for notifications relationship
    - Use selectinload() for ticket_logs relationship
    - Use joinedload() for assigned_worker relationship
  - Add comment: "// Eager loading strategies prevent N+1 queries during iteration"
  - Verify query executes in 2-3 queries total (1 main + N relationships via selectinload)
  - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6_

- [~] 6.4 Implement eager loading for notification retrieval
  - Update app/services/notification_service.py (or create if needed)
  - Add/update method: list_notifications_for_user(user_id)
  - Apply eager loading:
    - Use joinedload() for associated complaint relationship
  - Example: query = session.query(Notification).filter(...).options(joinedload('complaint'))
  - Add comment explaining eager loading
  - _Requirements: 7.7_

- [~] 6.5 Add PERFORMANCE_NOTES to service files
  - Add section to app/services/complaint_service.py:
    ```python
    # PERFORMANCE NOTES
    # - get_complaint_by_id(): Uses joinedload for assigned_worker, selectinload for notifications
    # - list_complaints(): Uses selectinload for notifications and ticket_logs to prevent N+1
    # - All queries are optimized for single execution per request
    ```
  - Add equivalent notes to app/services/notification_service.py
  - Document rationale for each eager loading choice
  - _Requirements: 7.9_

- [ ]* 6.6 Write property tests for eager loading
  - **Property 3: Query count consistency** - Query count remains constant regardless of complaint count (after initial query)
  - **Validates: Requirements 7.2, 7.3, 7.4**

- [ ]* 6.7 Write integration tests for N+1 query optimization
  - Test single complaint retrieval executes expected number of queries
  - Test complaint list retrieval doesn't trigger per-item queries
  - Test notification retrieval includes complaint data without extra queries
  - Use SQLAlchemy event listeners or mock to count database queries
  - Verify query count is O(1) or O(log n), not O(n) for n relationships
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

### Query Performance Verification

- [~] 6.8 Test all indexed queries execute efficiently
  - Audit query patterns in app/services/:
    - Complaint queries by status
    - Complaint queries by assigned_to (worker)
    - Complaint queries by created_at (temporal)
    - Notification queries by user_id
    - Ticket log queries by complaint_id
  - For each query, verify WHERE clause uses indexed column
  - Use EXPLAIN ANALYZE (if using PostgreSQL) to verify index usage
  - Document findings in PERFORMANCE_NOTES sections
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [~] 6.9 Implement query result caching where appropriate
  - Identify frequently-executed read-only queries (e.g., complaint status counts)
  - Implement Redis caching layer for results
  - Use cache key format: "query:{query_hash}" with TTL 5-15 minutes
  - Invalidate cache on related data updates (CUD operations)
  - Document caching strategy in PERFORMANCE_NOTES
  - _Requirements: 7.5_

- [~] 6.10 Checkpoint - Ensure performance optimization complete
  - Run full test suite verifying query counts
  - Verify no N+1 queries exist in complaint retrieval
  - Verify all indexes are being used
  - Ask the user if questions arise.

## Phase 7: Configuration & Documentation

### Environment Configuration

- [~] 7.1 Update app/config.py with all environment variables
  - Add configuration variables for all requirements:
    - MAX_LOGIN_ATTEMPTS (default: 5) - Req 2
    - LOGIN_RATE_LIMIT_WINDOW_SECONDS (default: 60) - Req 2
    - MAX_UPLOAD_SIZE_MB (default: 10) - Req 3
    - TOKEN_BLACKLIST_CLEANUP_HOUR (default: 2, UTC) - Req 4
    - TOKEN_BLACKLIST_CACHE_TTL_SECONDS (default: 300) - Req 4
    - EMAIL_VERIFICATION_ENABLED (default: true) - Req 5
    - VERIFICATION_TOKEN_EXPIRY_HOURS (default: 24) - Req 5
    - RESEND_EMAIL_RATE_LIMIT (default: 3) - Req 5
    - CORS_ALLOWED_ORIGINS (default: localhost:3000) - Req 8
    - PASSWORD_MIN_LENGTH (default: 12) - Req 8
    - PASSWORD_COMPLEXITY_REQUIRED (default: true) - Req 8
  - Read all from environment with sensible defaults
  - Validate values at app startup (fail if invalid)
  - Log configuration values at startup (excluding secrets)
  - _Requirements: 2.8, 3.10, 4.9, 5.11_

- [~] 7.2 Create .env.example with all configuration variables
  - Update .env.example with all new environment variables
  - Include comments explaining each variable
  - Use sensible default values
  - Do not include real secrets or credentials
  - Document min/max ranges where applicable
  - _Requirements: 2.8, 3.10, 4.9_

### Documentation

- [~] 7.3 Create IMPLEMENTATION_GUIDE.md
  - Document overall security architecture
  - Explain RBAC model and role definitions
  - Document token lifecycle (creation, blacklist, expiration)
  - Explain email verification flow
  - Document file upload validation process
  - Document rate limiting strategy
  - Include architecture diagrams (reference from design doc)
  - _Requirements: All_

- [~] 7.4 Add code comments to security-critical functions
  - Comment all functions in app/core/token_blacklist_middleware.py
  - Comment all functions in app/services/file_validator.py
  - Comment all functions in app/services/email_verification_service.py
  - Comment all functions in app/services/password_validator.py
  - Document preconditions, postconditions, and security implications
  - Document constant-time comparison usage for token verification
  - _Requirements: All_

- [~] 7.5 Update API documentation (OpenAPI/Swagger)
  - Add security scheme definition (bearer token)
  - Document all new endpoints: /auth/logout, /auth/verify, /auth/resend-verification-email
  - Document authentication requirements for existing endpoints
  - Add rate limit information to endpoint descriptions
  - Document error responses (400, 401, 403, 429, 500)
  - _Requirements: 1.8, 8_

## Phase 8: Integration & Verification

### Integration Testing

- [~] 8.1 Create comprehensive integration test suite
  - Create test file: tests/integration/test_security_hardening.py
  - Test complete user workflow:
    - Register user (email sent)
    - Verify email with token
    - Login with verified email
    - Create complaint
    - Upload file
    - Logout (token blacklisted)
    - Verify token rejected after logout
  - Test rate limiting across entire flow
  - _Requirements: All_

- [~] 8.2 Test all RBAC scenarios
  - Create test file: tests/integration/test_rbac_scenarios.py
  - Test each role accessing buildings endpoint:
    - Admin sees all buildings
    - Worker sees assigned buildings only
    - Student sees campus buildings only
    - Unauthenticated user gets 401
  - Test each role accessing complaints:
    - Admin sees all complaints
    - Worker sees assigned complaints
    - Student sees own complaints
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [~] 8.3 Test security headers and CORS
  - Create test file: tests/integration/test_security_headers.py
  - Test all security headers present on responses
  - Test CORS policy enforcement
  - Test cross-origin request rejection
  - Test invalid CORS origins denied
  - _Requirements: 8.9, 8.10, 8.12_

- [~] 8.4 Run full test suite with coverage
  - Execute: pytest tests/ --cov=app --cov-report=html
  - Verify code coverage > 90% for security-critical modules:
    - app/core/token_blacklist_middleware.py: > 95%
    - app/services/file_validator.py: > 95%
    - app/services/email_verification_service.py: > 95%
    - app/services/password_validator.py: > 95%
  - Fix coverage gaps
  - Generate coverage report: htmlcov/index.html
  - _Requirements: All_

### Performance Verification

- [~] 8.5 Benchmark query performance
  - Create performance test file: tests/performance/benchmark_queries.py
  - Test complaint retrieval performance:
    - Single complaint with relationships (should be 2-3 queries)
    - List of 100 complaints (should be 3 queries: complaints + eager loads)
  - Verify no N+1 query patterns
  - Document baseline performance numbers
  - _Requirements: 7.2, 7.3, 7.4_

- [~] 8.6 Benchmark file upload performance
  - Test upload endpoint with various file sizes (1MB, 5MB, 9.9MB)
  - Measure validation time separately from disk I/O
  - Verify upload < 5 second response time for 10MB file
  - _Requirements: 3.3_

- [~] 8.7 Verify token blacklist cache efficiency
  - Test token lookup with cache hit (should be <5ms Redis latency)
  - Test token lookup with cache miss (should fall back to PostgreSQL)
  - Verify cache repopulation on miss
  - _Requirements: 4.8_

### Deployment & Documentation

- [~] 8.8 Create deployment checklist
  - Document all database migrations needed
  - Document environment variables to configure
  - Document Redis configuration (cache size, TTL)
  - Document email service configuration (SMTP server)
  - Document backup/recovery procedures for token_blacklist table
  - Document monitoring/alerting for rate limit violations
  - _Requirements: All_

- [~] 8.9 Create operational runbook
  - Document how to rotate signing key for JWT tokens (if supported)
  - Document how to purge token_blacklist manually (if needed)
  - Document how to reset rate limit counters (if needed)
  - Document how to resend verification emails (support process)
  - Document security incident response procedures
  - _Requirements: All_

- [~] 8.10 Checkpoint - Final verification complete
  - Verify all tests pass (unit, integration, performance)
  - Verify code coverage > 90%
  - Verify no warnings in build logs
  - Verify documentation complete
  - Verify deployment checklist prepared
  - Ask the user if questions arise.


## Notes

### Task Execution Guidelines

- **Incremental Validation**: After completing each major phase (1-6), run tests to verify functionality before proceeding to next phase
- **Git Workflow**: Commit after each phase with message format: "feat(security): implement [phase-name]"
- **Optional Tasks**: Tasks marked with `*` are optional test-related tasks. They can be skipped for MVP but are recommended for production
- **Configuration First**: Complete Phase 7 (configuration) early to ensure all environment variables are available during implementation
- **Testing Throughout**: Don't defer testing to the end. Each feature should have tests written alongside implementation

### Key Implementation Notes

- **Password Hashing**: Use bcrypt with cost factor of 10-12 for production (adjust based on performance needs)
- **Token Hashing**: SHA-256 is appropriate for JWT blacklist (size: 64 hex chars). Never store raw tokens in database
- **Rate Limiting**: Redis SETEX with dynamic TTL provides automatic window reset. No background cleanup needed
- **Email Verification**: 24-hour token expiration balances security with user experience. Resend rate limit (3 per hour) prevents abuse
- **File Validation**: Magic number checking provides defense-in-depth even if extension is spoofed
- **Eager Loading**: selectinload() preferred for one-to-many (uses separate SELECT), joinedload() preferred for many-to-one (uses JOIN)
- **Error Handling**: Always log full details internally; return generic messages to client to prevent information disclosure
- **Logging**: Use structured logging with context (user_id, request_id) for correlation across logs

### Performance Targets

- **Token Blacklist Lookup**: < 5ms (should hit Redis cache)
- **File Validation**: < 100ms for 10MB file
- **Complaint List Query**: 3 queries max for any result size (1 main + 2 eager loads)
- **Login Rate Limit Check**: < 1ms (simple Redis INCR)
- **Email Verification**: < 500ms (hash comparison + database lookup)

### Security Considerations

- **Timing Attacks**: Use `hmac.compare_digest()` for all security-sensitive string comparisons
- **Information Disclosure**: Never expose which field validation failed (e.g., "email already exists")
- **XSS Prevention**: JSON encoding is sufficient for JSON responses. Don't store HTML/unescaped content
- **CSRF Protection**: FastAPI automatically includes CSRF protection. Configure CORS_ALLOWED_ORIGINS carefully
- **Secrets Management**: Never commit .env with real secrets. Use CI/CD secrets management
- **Token Rotation**: Consider implementing token refresh for long-lived sessions (out of scope for this spec)

### Backward Compatibility

- **New user.email_verified field**: Defaults to FALSE, existing users may need migration to set TRUE
- **New endpoints**: /auth/logout, /auth/verify, /auth/resend-verification-email don't conflict with existing
- **GET /buildings RBAC**: Adds permission checks but doesn't change response schema for authorized users
- **File validation**: Only applies to new uploads; existing files unaffected
- **Token blacklist**: Optional optimization; requests without blacklisted tokens work normally

### Testing Strategy

- **Unit Tests**: Test individual functions with mocked dependencies (Redis, database)
- **Integration Tests**: Test complete workflows with real dependencies (use test database)
- **Property-Based Tests**: Test invariants (e.g., RBAC idempotence, rate limit reset)
- **Performance Tests**: Benchmark query counts and response times
- **Security Tests**: Verify error messages don't leak information, CORS policy enforced

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5"]
    },
    {
      "id": 1,
      "tasks": ["1.7", "1.8", "1.9", "1.10", "2.1", "2.2"]
    },
    {
      "id": 2,
      "tasks": ["1.6", "1.11", "2.3", "2.4", "2.5", "2.8", "2.9"]
    },
    {
      "id": 3,
      "tasks": ["2.6", "2.7", "2.10", "2.11", "2.12", "3.1", "3.2", "3.3"]
    },
    {
      "id": 4,
      "tasks": ["3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "3.10", "3.11"]
    },
    {
      "id": 5,
      "tasks": ["3.12", "3.13", "4.1", "4.2"]
    },
    {
      "id": 6,
      "tasks": ["4.3", "4.4", "5.1", "5.2", "5.3", "5.4"]
    },
    {
      "id": 7,
      "tasks": ["4.5", "4.6", "5.5", "5.6", "5.7", "5.8", "5.9"]
    },
    {
      "id": 8,
      "tasks": ["5.10", "5.11", "5.12", "5.13", "6.1", "6.2"]
    },
    {
      "id": 9,
      "tasks": ["6.3", "6.4", "6.5", "6.6", "6.7"]
    },
    {
      "id": 10,
      "tasks": ["6.8", "6.9", "7.1", "7.2"]
    },
    {
      "id": 11,
      "tasks": ["7.3", "7.4", "7.5", "8.1", "8.2"]
    },
    {
      "id": 12,
      "tasks": ["8.3", "8.4", "8.5", "8.6", "8.7"]
    },
    {
      "id": 13,
      "tasks": ["8.8", "8.9", "8.10"]
    }
  ]
}
```

### Wave Explanation

- **Wave 0**: Database migrations (creates schema)
- **Wave 1**: SQLAlchemy models (defines data structures)
- **Wave 2**: Repository/service layer initialization + RBAC decorator
- **Wave 3**: Token blacklist + rate limiter implementation + building endpoint
- **Wave 4**: Email verification core services
- **Wave 5**: Email endpoint implementations
- **Wave 6**: File validator + input validation core
- **Wave 7**: Error handling, password validation, CORS, security headers
- **Wave 8**: Security tests + eager loading setup
- **Wave 9**: Eager loading implementation + query optimization
- **Wave 10**: Performance verification + configuration
- **Wave 11**: Documentation + integration tests begin
- **Wave 12**: Final integration/performance tests
- **Wave 13**: Deployment preparation + final verification

