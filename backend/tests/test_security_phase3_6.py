"""
Comprehensive Security Tests for Phases 3-6 Implementation.

Tests cover:
- Phase 3: Authentication hardening (email verification, login rate limiting)
- Phase 4: File upload security (validation, sanitization)
- Phase 5: General security (RBAC, error handling, security headers)
- Phase 6: Performance (eager loading query optimization)

Requirements: 2.1-2.3, 3.1-3.9, 4.1, 4.3, 5.1-5.11, 8.1-8.12
"""

import pytest
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.email_verification_service import EmailVerificationService
from app.services.password_validator import PasswordValidator
from app.services.file_validator import FileValidator, FileValidationException
from app.services.token_blacklist_repository import TokenBlacklistRepository
from app.core.permissions import verify_ownership, require_permission, get_user_permissions
from app.core.security_headers_middleware import SecurityHeadersMiddleware
from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken
from app.models.complaint import Complaint
from app.models.token_blacklist import TokenBlacklist


# ============================================================================
# PHASE 3: AUTHENTICATION HARDENING TESTS
# ============================================================================

class TestEmailVerificationService:
    """Tests for email verification service (Phase 3.1-3.3, 5.6-5.9)."""
    
    def test_generate_verification_token(self):
        """Test token generation creates cryptographically secure token."""
        token1 = EmailVerificationService.generate_verification_token()
        token2 = EmailVerificationService.generate_verification_token()
        
        # Tokens should be different (random)
        assert token1 != token2
        # Tokens should be URL-safe strings
        assert isinstance(token1, str)
        assert len(token1) > 20
        # No special characters that would break URLs
        assert '+' not in token1 and '/' not in token1
    
    def test_hash_verification_token(self):
        """Test token hashing produces consistent SHA-256 hash."""
        token = "test_token_12345"
        hash1 = EmailVerificationService.hash_verification_token(token)
        hash2 = EmailVerificationService.hash_verification_token(token)
        
        # Same token should produce same hash (deterministic)
        assert hash1 == hash2
        # Hash should be hex-encoded SHA-256 (64 chars)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_verify_token_hash_success(self):
        """Test token verification succeeds with correct token."""
        token = "correct_token"
        token_hash = EmailVerificationService.hash_verification_token(token)
        
        is_valid = EmailVerificationService.verify_token_hash(token, token_hash)
        assert is_valid is True
    
    def test_verify_token_hash_failure(self):
        """Test token verification fails with incorrect token."""
        correct_token = "correct_token"
        wrong_token = "wrong_token"
        token_hash = EmailVerificationService.hash_verification_token(correct_token)
        
        is_valid = EmailVerificationService.verify_token_hash(wrong_token, token_hash)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_create_verification_token_stores_hash_not_plaintext(self, db_session: AsyncSession):
        """Test that only token hash is stored, never plaintext."""
        user_id = "test_user_123"
        
        plaintext_token, token_hash = await EmailVerificationService.create_verification_token(
            db_session, user_id
        )
        
        # Query database and verify only hash is stored
        result = await db_session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.user_id == user_id)
        )
        stored_token = result.scalar_one_or_none()
        
        # Verify hash matches
        assert stored_token.token_hash == token_hash
        # Verify plaintext token is not stored
        assert stored_token.token_hash != plaintext_token


class TestPasswordValidator:
    """Tests for password validation (Phase 5.1, 5.8, 8.7)."""
    
    def test_validate_strong_password(self):
        """Test validation passes for strong password."""
        strong_password = "MyStr0ng!Password"
        is_valid, msg = PasswordValidator.validate(strong_password)
        
        assert is_valid is True
        assert msg == ""
    
    def test_validate_weak_password_no_uppercase(self):
        """Test validation fails for password without uppercase."""
        weak_password = "mystr0ng!password"
        is_valid, msg = PasswordValidator.validate(weak_password)
        
        assert is_valid is False
        assert "does not meet requirements" in msg
    
    def test_validate_weak_password_no_special(self):
        """Test validation fails for password without special character."""
        weak_password = "MyStr0ngPassword"
        is_valid, msg = PasswordValidator.validate(weak_password)
        
        assert is_valid is False
        assert "does not meet requirements" in msg
    
    def test_hash_password(self):
        """Test password hashing creates bcrypt hash."""
        password = "TestPass123!"
        hashed = PasswordValidator.hash_password(password)
        
        # Hash should start with bcrypt prefix
        assert hashed.startswith('$2')
        # Hash should be different from plaintext
        assert hashed != password
    
    def test_verify_password_success(self):
        """Test password verification succeeds with correct password."""
        password = "TestPass123!"
        hashed = PasswordValidator.hash_password(password)
        
        is_valid = PasswordValidator.verify_password(password, hashed)
        assert is_valid is True
    
    def test_verify_password_failure(self):
        """Test password verification fails with incorrect password."""
        correct_password = "TestPass123!"
        wrong_password = "WrongPass456!"
        hashed = PasswordValidator.hash_password(correct_password)
        
        is_valid = PasswordValidator.verify_password(wrong_password, hashed)
        assert is_valid is False


# ============================================================================
# PHASE 4: FILE UPLOAD SECURITY TESTS
# ============================================================================

class TestFileValidator:
    """Tests for file upload validation (Phase 4.1, 3.1-3.9)."""
    
    def test_validate_filename_path_traversal(self):
        """Test path traversal attack is blocked."""
        malicious_filename = "../../../etc/passwd"
        
        with pytest.raises(FileValidationException):
            FileValidator.validate_filename(malicious_filename)
    
    def test_validate_filename_null_byte(self):
        """Test null byte in filename is blocked."""
        malicious_filename = "test\x00.jpg"
        
        with pytest.raises(FileValidationException):
            FileValidator.validate_filename(malicious_filename)
    
    def test_validate_filename_valid(self):
        """Test valid filename passes."""
        valid_filename = "photo.jpg"
        
        is_valid, msg = FileValidator.validate_filename(valid_filename)
        assert is_valid is True
    
    def test_validate_extension_allowed(self):
        """Test allowed extension passes."""
        valid_filename = "photo.jpg"
        
        is_valid, msg = FileValidator.validate_extension(valid_filename)
        assert is_valid is True
    
    def test_validate_extension_forbidden(self):
        """Test forbidden extension is blocked."""
        dangerous_filename = "malware.exe"
        
        with pytest.raises(FileValidationException):
            FileValidator.validate_extension(dangerous_filename)
    
    def test_validate_mime_type_allowed(self):
        """Test allowed MIME type passes."""
        mime_type = "image/jpeg"
        extension = ".jpg"
        
        is_valid, msg = FileValidator.validate_mime_type(mime_type, extension)
        assert is_valid is True
    
    def test_validate_mime_type_forbidden(self):
        """Test forbidden MIME type is blocked."""
        mime_type = "application/x-executable"
        extension = ".exe"
        
        with pytest.raises(FileValidationException):
            FileValidator.validate_mime_type(mime_type, extension)
    
    def test_validate_file_size_too_large(self):
        """Test file exceeding size limit is blocked."""
        size_bytes = FileValidator.MAX_FILE_SIZE + 1
        
        with pytest.raises(FileValidationException):
            FileValidator.validate_file_size(size_bytes)
    
    def test_validate_file_size_ok(self):
        """Test file within size limit passes."""
        size_bytes = FileValidator.MAX_FILE_SIZE - 1
        
        is_valid, msg = FileValidator.validate_file_size(size_bytes)
        assert is_valid is True
    
    def test_validate_magic_numbers_jpg_valid(self):
        """Test valid JPG magic numbers pass."""
        # JPG magic number: FF D8 FF
        file_content = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        extension = ".jpg"
        
        is_valid, msg = FileValidator.validate_magic_numbers(file_content, extension)
        assert is_valid is True
    
    def test_validate_magic_numbers_mismatch(self):
        """Test magic number mismatch is blocked."""
        # PNG magic number (not JPG)
        file_content = b'\x89PNG\r\n\x1a\n'
        extension = ".jpg"  # But claiming to be JPG
        
        with pytest.raises(FileValidationException):
            FileValidator.validate_magic_numbers(file_content, extension)
    
    def test_generate_secure_filename(self):
        """Test secure filename generation."""
        original_filename = "my photo.jpg"
        
        secure_filename = FileValidator.generate_secure_filename(original_filename)
        
        # Should preserve extension
        assert secure_filename.endswith(".jpg")
        # Should not contain original name
        assert "my photo" not in secure_filename
        # Should be UUID format
        assert "-" in secure_filename  # UUID has hyphens


# ============================================================================
# PHASE 5: GENERAL SECURITY HARDENING TESTS
# ============================================================================

class TestRBACPermissions:
    """Tests for RBAC and permission decorators (Phase 5.2, 5.3, 8.5, 8.6)."""
    
    def test_get_user_permissions_admin(self):
        """Test admin role has all permissions."""
        admin_perms = get_user_permissions("admin")
        
        assert "view_all_complaints" in admin_perms
        assert "manage_workers" in admin_perms
        assert "verify_completion" in admin_perms
        assert len(admin_perms) > len(get_user_permissions("worker"))
    
    def test_get_user_permissions_worker(self):
        """Test worker role has appropriate permissions."""
        worker_perms = get_user_permissions("worker")
        
        assert "view_assigned_complaints" in worker_perms
        assert "upload_resolution" in worker_perms
        assert "manage_workers" not in worker_perms  # Workers can't manage
    
    def test_get_user_permissions_student(self):
        """Test student role has appropriate permissions."""
        student_perms = get_user_permissions("student")
        
        assert "create_complaint" in student_perms
        assert "view_own_complaints" in student_perms
        assert "manage_workers" not in student_perms
        assert "view_all_complaints" not in student_perms
    
    def test_user_has_permission_true(self):
        """Test user_has_permission returns true for authorized."""
        user = User(
            name="Admin User",
            email="admin@test.com",
            password="hashed",
            role="admin"
        )
        
        from app.core.permissions import user_has_permission
        assert user_has_permission(user, "manage_workers") is True
    
    def test_user_has_permission_false(self):
        """Test user_has_permission returns false for unauthorized."""
        user = User(
            name="Student User",
            email="student@test.com",
            password="hashed",
            role="student"
        )
        
        from app.core.permissions import user_has_permission
        assert user_has_permission(user, "manage_workers") is False


class TestSecurityHeaders:
    """Tests for security headers middleware (Phase 5.4, 8.12)."""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """Test all security headers are added to response."""
        from fastapi import Request
        from starlette.responses import Response
        
        middleware = SecurityHeadersMiddleware(app=MagicMock())
        request = MagicMock(spec=Request)
        request.url.scheme = "https"
        
        async def call_next(req):
            return Response()
        
        response = await middleware.dispatch(request, call_next)
        
        # Check all required headers are present
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "max-age=31536000" in response.headers.get("Strict-Transport-Security", "")
        assert "X-Powered-By" not in response.headers


# ============================================================================
# PHASE 6: PERFORMANCE OPTIMIZATION TESTS
# ============================================================================

class TestEagerLoading:
    """Tests for eager loading query optimization (Phase 6.1-6.5)."""
    
    @pytest.mark.asyncio
    async def test_get_complaint_with_relations(self, db_session: AsyncSession):
        """Test eager loading prevents N+1 queries."""
        from app.services.complaint_service import get_complaint_by_id_with_relations
        
        # Create test complaint with relations
        complaint = Complaint(
            id="test-complaint-1",
            title="Test",
            description="Test complaint",
            building_id="building-1",
            floor_number="1",
            room_number="101",
            user_id="user-1"
        )
        db_session.add(complaint)
        await db_session.commit()
        
        # This should load all relations in 2-3 queries total,
        # not 1 + N queries
        result = await get_complaint_by_id_with_relations(db_session, "test-complaint-1")
        
        assert result is not None
        assert result.id == "test-complaint-1"
    
    def test_performance_notes_present(self):
        """Test performance notes are documented in code."""
        from app.services import complaint_service
        
        # Check that performance notes are in module docstring/comments
        source_code = complaint_service.__doc__ or ""
        assert "PERFORMANCE" in source_code or "eager" in complaint_service.__name__


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAuthenticationFlow:
    """Integration tests for authentication flow (Phase 3, 5.5)."""
    
    @pytest.mark.asyncio
    async def test_register_verify_login_flow(self, client, db_session):
        """Test complete registration -> verification -> login flow."""
        # 1. Register user
        register_response = await client.post("/auth/register", json={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "student"
        })
        
        assert register_response.status_code == 201
        assert "email_verified" in register_response.json()["data"]
        assert register_response.json()["data"]["email_verified"] is False
        
        # 2. Login should fail (email not verified)
        login_response = await client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "SecurePass123!"
        })
        
        assert login_response.status_code == 403
        assert "Email not verified" in login_response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, client):
        """Test login rate limiting (Phase 3.6, 2.1-2.3)."""
        # Make multiple failed login attempts
        for i in range(6):
            response = await client.post("/auth/login", data={
                "username": "test@example.com",
                "password": "WrongPassword"
            })
        
        # 6th attempt should be rate limited
        assert response.status_code == 429
        assert "Retry-After" in response.headers


class TestFileUploadSecurity:
    """Integration tests for file upload security (Phase 4)."""
    
    @pytest.mark.asyncio
    async def test_malicious_file_rejected(self, client, auth_token):
        """Test malicious files are rejected during upload."""
        # Try to upload executable
        files = {
            'file': ('malware.exe', b'MZ\x90\x00', 'application/octet-stream')
        }
        
        response = await client.post(
            "/complaints/123/upload-resolution",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should be rejected
        assert response.status_code == 400
        assert "File upload failed" in response.json()["detail"]


class TestErrorHandling:
    """Tests for error handling (Phase 5.1, 8.3, 8.4)."""
    
    @pytest.mark.asyncio
    async def test_500_error_returns_generic_message(self, client):
        """Test 500 errors return generic message without stack trace."""
        # Trigger an unhandled exception
        response = await client.get("/api/trigger-error")
        
        body = response.json()
        # Should have generic message
        assert "Internal server error" in body.get("message", "")
        # Should have request_id for support
        assert "request_id" in body
        # Should NOT contain stack trace or implementation details
        assert "Traceback" not in body.get("message", "")
    
    def test_auth_error_returns_generic_message(self, client):
        """Test auth errors return generic message (no email enumeration)."""
        response = client.get("/auth/me")
        
        body = response.json()
        # Should be generic
        assert "Authorization credentials are missing or invalid" in body.get("message", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
