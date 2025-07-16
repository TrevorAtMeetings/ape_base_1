
import logging
import base64
import io
from PIL import Image
from pdf2image import convert_from_path
from typing import List

logger = logging.getLogger(__name__)

def convert_pdf_to_images(pdf_path: str, max_pages: int = 3) -> List[str]:
    """
    Convert PDF pages to base64 encoded JPEG images
    
    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to convert
        
    Returns:
        List of base64 encoded image strings
    """
    try:
        logger.info(f"[PDF Converter] Converting PDF: {pdf_path}")
        
        # Convert PDF to images with optimized settings
        images = convert_from_path(
            pdf_path,
            dpi=150,  # Reduced from 200 for faster processing
            fmt='JPEG',
            first_page=1,
            last_page=max_pages
        )
        
        logger.info(f"[PDF Converter] Converted {len(images)} pages")
        
        base64_images = []
        
        for i, image in enumerate(images):
            logger.info(f"[PDF Converter] Processing page {i+1}: {image.width}x{image.height}")
            
            # Optimize image size for API
            max_size = 1536
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"[PDF Converter] Resized page {i+1} to: {new_size}")
            
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', optimize=True, quality=85)
            img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            base64_images.append(img_data)
            
            # Log size for monitoring
            size_kb = len(img_data) * 3 / 4 / 1024  # Approximate size in KB
            logger.info(f"[PDF Converter] Page {i+1} base64 size: {size_kb:.1f} KB")
        
        logger.info(f"[PDF Converter] Successfully converted {len(base64_images)} pages")
        return base64_images
        
    except Exception as e:
        logger.error(f"[PDF Converter] Failed to convert PDF: {e}")
        raise ValueError(f"PDF conversion failed: {e}")
