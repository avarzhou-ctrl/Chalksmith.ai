import os
import tempfile
from typing import Optional
from fastapi import UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
import shutil

async def extract_source_context(file: Optional[UploadFile]) -> Optional[str]:
    if file is None or not file.filename:
        return None

    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as buffer:
        shutil.copyfileobj(file.file, buffer)
        temp_path = buffer.name

    try:
        loader = PyMuPDFLoader(temp_path)
        documents = loader.load()
        
        full_text = "\n\n".join([doc.page_content for doc in documents])
        
        return full_text
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
