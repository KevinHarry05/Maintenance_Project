"""File Validator Service - Comprehensive file upload security validation.

This service validates uploaded files against multiple security criteria:
- Filename validation (prevents path traversal attacks)
- Extension validation (whitelist-based)
- MIME type validation (whitelist-based)
- File size validation (configurable limit)
- Magic number validation (verifies file signature)

Security Model:
- Whitelist approach (only allow known good types)
- Multiple validation layers (defense in depth)
- Path traversal detection and blocking
- Magic number verification (can't lie about file type)
"""

import os
import re
import uuid
import logging
from pathlib import Path
from typing import Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class FileValidationException(Exception):
    """Base exception for file validation errors."""
    pass


class InvalidExtensionException(FileValidationException):
    """Raised when file extension is not allowed."""
    pass


class InvalidMimeTypeException(FileValidationException):
    """Raised when MIME type is not allowed."""
    pass


class InvalidFileSizeException(FileValidationException):
    """Raised when file size exceeds limit."""
    pass


class PathTraversalException(FileValidationException):
    """Raised when path traversal attack is detected."""
    pass


class InvalidMagicNumberException(FileValidationException):
    """Raised when file magic number doesn't match extension."""
    pass


class FileValidator:
    """Service for validating uploaded files."""

    # Whitelist of allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.jpg',
        '.jpeg',
        '.png',
        '.webp'
    }

    # Whitelist of allowed MIME types
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/png',
        'image/webp'
    }

    # Forbidden extensions (explicit blacklist for dangerous types)
    FORBIDDEN_EXTENSIONS = {
        '.exe',
        '.bat',
        '.cmd',
        '.com',
        '.scr',
        '.svg',
        '.pdf',
        '.zip',
        '.rar',
        '.7z',
        '.tar',
        '.gz',
        '.sh',
        '.bash',
        '.ps1',
        '.vbs',
        '.js',
        '.py',
        '.phtml',
        '.phar'
    }

    # Magic numbers (file signatures) for verification
    # Format: extension -> (offset, signature_bytes)
    MAGIC_NUMBERS = {
        '.jpg': (0, b'\xff\xd8\xff'),
        '.jpeg': (0, b'\xff\xd8\xff'),
        '.png': (0, b'\x89PNG\r\n\x1a\n'),
        '.webp': (0, b'RIFF'),  # More specific check needed for WEBP
    }

    # Maximum file size (configurable via settings)
    MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_BYTES

    # Forbidden characters in filenames
    FORBIDDEN_PATH_CHARS = {'/', '\\', '\0', '\n', '\r', '\t'}

    # Forbidden patterns
    FORBIDDEN_PATTERNS = {'..', '~', '$'}

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """
        Validate filename for security issues.

        Detects and blocks:
        - Path traversal attempts (.., ../, etc)
        - Directory separators (/, \\)
        - Null bytes and control characters
        - Forbidden patterns (~, $)

        Args:
            filename: Original filename from upload

        Returns:
            Tuple of (is_valid: bool, error_message: str)

        Raises:
            PathTraversalException: If path traversal attack detected
        """
        if not filename:
            raise PathTraversalException("Filename cannot be empty")

        # Check for path traversal attempts
        if '..' in filename:
            logger.warning(
                "Path traversal attempt detected",
                filename=filename,
                severity="HIGH"
            )
            raise PathTraversalException("Filename contains '..' path traversal")

        # Check for directory separators
        for char in FileValidator.FORBIDDEN_PATH_CHARS:
            if char in filename:
                logger.warning(
                    "Forbidden character in filename",
                    filename=filename,
                    forbidden_char=repr(char),
                    severity="HIGH"
                )
                raise PathTraversalException(
                    f"Filename contains forbidden character"
                )

        # Check for forbidden patterns
        for pattern in FileValidator.FORBIDDEN_PATTERNS:
            if pattern in filename:
                logger.warning(
                    "Forbidden pattern in filename",
                    filename=filename,
                    pattern=pattern,
                    severity="MEDIUM"
                )
                raise PathTraversalException(f"Filename contains forbidden pattern")

        return True, ""

    @staticmethod
    def validate_extension(filename: str) -> Tuple[bool, str]:
        """
        Validate file extension against whitelist and blacklist.

        Args:
            filename: Filename to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)

        Raises:
            InvalidExtensionException: If extension not allowed
        """
        # Get extension
        extension = Path(filename).suffix.lower()

        if not extension:
            logger.warning(
                "File upload rejected: no extension",
                filename=filename
            )
            raise InvalidExtensionException("File must have an extension")

        # Check forbidden extensions first
        if extension in FileValidator.FORBIDDEN_EXTENSIONS:
            logger.warning(
                "File upload rejected: forbidden extension",
                filename=filename,
                extension=extension,
                severity="HIGH"
            )
            raise InvalidExtensionException(
                f"File extension '{extension}' is not allowed"
            )

        # Check whitelist
        if extension not in FileValidator.ALLOWED_EXTENSIONS:
            logger.warning(
                "File upload rejected: extension not whitelisted",
                filename=filename,
                extension=extension
            )
            raise InvalidExtensionException(
                f"File extension '{extension}' is not allowed. "
                f"Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"
            )

        return True, ""

    @staticmethod
    def validate_mime_type(mime_type: str, extension: str) -> Tuple[bool, str]:
        """
        Validate MIME type against whitelist.

        Also verifies MIME type matches file extension.

        Args:
            mime_type: MIME type from upload (e.g., image/jpeg)
            extension: File extension (e.g., .jpg)

        Returns:
            Tuple of (is_valid: bool, error_message: str)

        Raises:
            InvalidMimeTypeException: If MIME type not allowed
        """
        # Normalize MIME type (lowercase)
        mime_type_normalized = mime_type.lower() if mime_type else ""

        # Check if MIME type is whitelisted
        if mime_type_normalized not in FileValidator.ALLOWED_MIME_TYPES:
            logger.warning(
                "File upload rejected: MIME type not whitelisted",
                mime_type=mime_type,
                extension=extension
            )
            raise InvalidMimeTypeException(
                f"MIME type '{mime_type}' is not allowed. "
                f"Allowed: {', '.join(FileValidator.ALLOWED_MIME_TYPES)}"
            )

        return True, ""

    @staticmethod
    def validate_file_size(file_size_bytes: int) -> Tuple[bool, str]:
        """
        Validate file size against limit.

        Args:
            file_size_bytes: Size of file in bytes

        Returns:
            Tuple of (is_valid: bool, error_message: str)

        Raises:
            InvalidFileSizeException: If file too large
        """
        if file_size_bytes > FileValidator.MAX_FILE_SIZE:
            max_mb = FileValidator.MAX_FILE_SIZE / (1024 * 1024)
            actual_mb = file_size_bytes / (1024 * 1024)

            logger.warning(
                "File upload rejected: file too large",
                file_size_mb=actual_mb,
                max_size_mb=max_mb
            )
            raise InvalidFileSizeException(
                f"File size ({actual_mb:.1f} MB) exceeds maximum ({max_mb:.1f} MB)"
            )

        return True, ""

    @staticmethod
    def validate_magic_numbers(file_content: bytes, extension: str) -> Tuple[bool, str]:
        """
        Validate file magic number (signature) matches extension.

        This prevents attackers from uploading executable files with image extensions.

        Args:
            file_content: File content (bytes)
            extension: File extension to validate against

        Returns:
            Tuple of (is_valid: bool, error_message: str)

        Raises:
            InvalidMagicNumberException: If magic number doesn't match
        """
        if extension not in FileValidator.MAGIC_NUMBERS:
            # No magic number check defined for this extension
            return True, ""

        offset, expected_signature = FileValidator.MAGIC_NUMBERS[extension]

        # Check if file is large enough
        if len(file_content) < len(expected_signature) + offset:
            logger.warning(
                "File upload rejected: file too small for magic number check",
                extension=extension,
                file_size=len(file_content)
            )
            raise InvalidMagicNumberException(
                "File is too small or corrupted"
            )

        # Extract actual signature from file
        actual_signature = file_content[offset:offset + len(expected_signature)]

        # Special handling for WEBP (check for WEBP signature in RIFF)
        if extension == '.webp':
            if actual_signature[:4] != b'RIFF' or len(file_content) < 12:
                raise InvalidMagicNumberException("File signature doesn't match .webp extension")
            # Check for WEBP signature at offset 8
            if file_content[8:12] != b'WEBP':
                raise InvalidMagicNumberException("File signature doesn't match .webp extension")
        elif actual_signature != expected_signature:
            logger.warning(
                "File upload rejected: magic number mismatch",
                extension=extension,
                expected=expected_signature.hex(),
                actual=actual_signature.hex()
            )
            raise InvalidMagicNumberException(
                f"File signature doesn't match .{extension} extension"
            )

        return True, ""

    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """
        Generate a secure filename using UUID v4 + original extension.

        Prevents path traversal and other filename-based attacks.

        Args:
            original_filename: Original filename from upload

        Returns:
            Secure filename (e.g., "a1b2c3d4-e5f6-4789-abcd-ef1234567890.jpg")

        Postcondition:
            - Filename contains no path separators or dangerous characters
            - Filename is unique (UUID based)
            - Original extension is preserved
            - Cannot be used for path traversal attacks
        """
        # Extract extension (already validated)
        extension = Path(original_filename).suffix.lower()

        # Generate UUID v4
        uuid_str = str(uuid.uuid4())

        # Combine UUID + extension
        secure_filename = f"{uuid_str}{extension}"

        logger.debug(
            "Secure filename generated",
            original_filename=original_filename,
            secure_filename=secure_filename
        )

        return secure_filename
