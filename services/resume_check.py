import os
import shutil
from datetime import datetime

from fastapi import HTTPException, UploadFile, status
import pdfplumber


MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
MAX_PAGES = 2
TEMP_DIR = "resume_temp_folder"

os.makedirs(TEMP_DIR, exist_ok=True)


def check_and_save_resume(file: UploadFile) -> tuple[str, str, str]:
    filename = file.filename or ""

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required."
        )

    name, ext = os.path.splitext(filename)

    # Extension validation
    if ext.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Only PDF file is allowed."
        )

    # MIME type validation
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid file content type."
        )

    # File size validation
    file.file.seek(0, 2)  # it moves the pointer to the end of file, therefore no need of loading entire file in memory
    file_size = file.file.tell()   # asking where the pointer is, which will give size in bytes till pointer
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5 MB limit."
        )

    # PDF signature validation
    header = file.file.read(5)

    if header != b"%PDF-":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a valid PDF file."
        )

    file.file.seek(0)

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    unique_filename = f"{name}_{timestamp}{ext.lower()}"

    file_path = os.path.join(
        TEMP_DIR,
        unique_filename
    )

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # PDF validation + text extraction
    try:
        with pdfplumber.open(file_path) as pdf:

            page_count = len(pdf.pages)

            if page_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF contains no pages."
                )

            if page_count > MAX_PAGES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Resume exceeds maximum allowed pages ({MAX_PAGES})."
                )

            text = ""

            for page in pdf.pages:
                text += page.extract_text() or ""

            if len(text.strip()) < 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF contains insufficient text."
                )

    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or unreadable PDF."
        )

    return unique_filename, file_path, text