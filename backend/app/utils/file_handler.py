from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from fastapi import UploadFile


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


async def save_complaint_file(file: UploadFile | None, upload_dir: str) -> str | None:
	if file is None:
		return None

	destination_dir = Path(upload_dir)
	destination_dir.mkdir(parents=True, exist_ok=True)

	extension = Path(file.filename or "").suffix
	if extension.lower() not in ALLOWED_EXTENSIONS:
		raise HTTPException(status_code=400, detail="Invalid file type")

	safe_name = f"{uuid4()}{extension}"
	destination = destination_dir / safe_name

	contents = await file.read()
	if len(contents) > MAX_FILE_SIZE_BYTES:
		raise HTTPException(status_code=413, detail="File too large")

	destination.write_bytes(contents)

	return str(destination).replace('\\', '/')
