from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class UserResponse(BaseModel):
	id: UUID
	name: str
	email: EmailStr
	role: str
	created_at: datetime

	class Config:
		from_attributes = True
	
	# Phase 5.7: Add field validators (Requirement 8.1)
	@field_validator('email')
	@classmethod
	def validate_email(cls, v):
		"""Validate email format."""
		if not v or len(v) == 0:
			raise ValueError('Email cannot be empty')
		if len(v) > 255:
			raise ValueError('Email must not exceed 255 characters')
		return v.lower()
	
	@field_validator('name')
	@classmethod
	def validate_name(cls, v):
		"""Validate name is reasonable length."""
		if not v or len(v.strip()) == 0:
			raise ValueError('Name cannot be empty')
		if len(v) < 2:
			raise ValueError('Name must be at least 2 characters')
		if len(v) > 200:
			raise ValueError('Name must not exceed 200 characters')
		return v.strip()
	
	@field_validator('role')
	@classmethod
	def validate_role(cls, v):
		"""Validate role is one of allowed values."""
		allowed_roles = {"admin", "worker", "student"}
		if v not in allowed_roles:
			raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
		return v
