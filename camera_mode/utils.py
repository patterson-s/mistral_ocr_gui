import tempfile
import os
from typing import List, BinaryIO
from io import BytesIO

def create_temp_file(file_data: BinaryIO, filename: str) -> str:
    """Create a temporary file from binary data"""
    suffix = os.path.splitext(filename)[1] if '.' in filename else '.jpg'
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        file_data.seek(0)
        tmp_file.write(file_data.read())
        return tmp_file.name

def cleanup_temp_files(file_paths: List[str]) -> None:
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass  # Ignore cleanup errors

def validate_image_format(file_data: BytesIO) -> bool:
    """Validate if the file is a supported image format"""
    try:
        from PIL import Image
        file_data.seek(0)
        img = Image.open(file_data)
        img.verify()
        return True
    except Exception:
        return False

def get_image_info(file_data: BytesIO) -> dict:
    """Get basic information about an image"""
    try:
        from PIL import Image
        file_data.seek(0)
        img = Image.open(file_data)
        
        return {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height
        }
    except Exception:
        return {}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"