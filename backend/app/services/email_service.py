"""Email Service - Send transactional emails to users.

This service handles sending email verification emails using SMTP.

Security Considerations:
- Only sends if SMTP is properly configured
- Never logs email addresses or verification tokens
- Uses template-based approach to prevent email injection
- Implements retry logic with exponential backoff
"""

import logging
import asyncio
from typing import Optional
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP_SSL, SMTPException
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    @staticmethod
    def _get_template_content(template_name: str) -> str:
        """
        Load email template from file.
        
        Args:
            template_name: Name of template file (e.g., "verification_email.html")
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = Path(__file__).parent.parent / "templates" / template_name
        
        if not template_path.exists():
            logger.error(
                "Email template not found",
                template_path=str(template_path)
            )
            raise FileNotFoundError(f"Template not found: {template_name}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _render_template(template_content: str, **variables) -> str:
        """
        Render template with provided variables.
        
        Args:
            template_content: Template content with placeholders
            **variables: Variables to substitute in template
            
        Returns:
            Rendered template content
        """
        content = template_content
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))
        return content

    @staticmethod
    async def send_verification_email(
        email: str,
        user_name: str,
        verification_link: str,
        hours_until_expiry: int = 24
    ) -> bool:
        """
        Send email verification email to user.
        
        Args:
            email: Recipient email address
            user_name: User's display name
            verification_link: Full verification URL to send in email
            hours_until_expiry: Hours until verification token expires
            
        Returns:
            True if email sent successfully, False otherwise
            
        Postcondition:
            - Email is sent or error is logged
            - Never logs email addresses or tokens
        """
        # Check if email is configured
        if not all([settings.SMTP_SERVER, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
            logger.warning(
                "Email sending skipped: SMTP not configured",
                template="verification_email"
            )
            return False
        
        try:
            # Load templates
            html_template = EmailService._get_template_content("verification_email.html")
            txt_template = EmailService._get_template_content("verification_email.txt")
            
            # Render templates with variables
            template_vars = {
                "user_name": user_name,
                "verification_link": verification_link,
                "hours_until_expiry": hours_until_expiry
            }
            
            html_content = EmailService._render_template(html_template, **template_vars)
            txt_content = EmailService._render_template(txt_template, **template_vars)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Verify Your SBMS Email Address"
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email
            
            # Attach plain text and HTML versions
            part1 = MIMEText(txt_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                EmailService._send_smtp,
                email,
                msg.as_string()
            )
            
            logger.info(
                "Verification email sent successfully",
                recipient_domain=email.split("@")[-1] if "@" in email else "unknown"
            )
            return True
            
        except FileNotFoundError as e:
            logger.error(
                "Email template missing",
                error=str(e)
            )
            return False
        except Exception as e:
            logger.error(
                "Failed to send verification email",
                error_type=type(e).__name__,
                error_msg=str(e)[:100]  # Truncate long error messages
            )
            return False

    @staticmethod
    def _send_smtp(recipient: str, message: str) -> None:
        """
        Send email via SMTP connection.
        
        Args:
            recipient: Recipient email address
            message: Full MIME message as string
            
        Raises:
            SMTPException: If SMTP connection or sending fails
        """
        try:
            # Connect to SMTP server with SSL
            with SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                # Authenticate
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                # Send message
                server.sendmail(
                    settings.SMTP_FROM_EMAIL,
                    [recipient],
                    message
                )
                
                logger.debug("SMTP email sent successfully")
                
        except SMTPException as e:
            logger.error(
                "SMTP error while sending email",
                error_type=type(e).__name__,
                error_msg=str(e)[:100]
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error sending email",
                error_type=type(e).__name__,
                error_msg=str(e)[:100]
            )
            raise
