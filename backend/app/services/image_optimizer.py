"""
Image Optimization Service for ErgoLab
Handles image compression and thumbnail generation
"""
from PIL import Image
import io
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Service for optimizing images before storage"""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'JPEG', 'PNG', 'GIF', 'WEBP', 'BMP'}
    
    # Default settings
    DEFAULT_MAX_SIZE = (1920, 1080)
    DEFAULT_THUMBNAIL_SIZE = (300, 300)
    DEFAULT_QUALITY = 85
    THUMBNAIL_QUALITY = 80
    
    @staticmethod
    def is_supported_image(content_type: str) -> bool:
        """Check if the content type is a supported image format"""
        return content_type.startswith('image/')
    
    @staticmethod
    def _convert_to_rgb(img: Image.Image) -> Image.Image:
        """Convert image to RGB mode for JPEG compatibility"""
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparency
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA' or (img.mode == 'P' and 'transparency' in img.info):
                # Handle transparency
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            return background
        elif img.mode != 'RGB':
            return img.convert('RGB')
        return img
    
    @classmethod
    def optimize_image(
        cls,
        image_bytes: bytes,
        max_size: Tuple[int, int] = None,
        quality: int = None,
        format: str = 'JPEG'
    ) -> Tuple[bytes, dict]:
        """
        Optimize image size and quality
        
        Args:
            image_bytes: Raw image bytes
            max_size: Maximum dimensions (width, height)
            quality: JPEG quality (1-100)
            format: Output format (JPEG, PNG, WEBP)
        
        Returns:
            Tuple of (optimized_bytes, metadata_dict)
        """
        max_size = max_size or cls.DEFAULT_MAX_SIZE
        quality = quality or cls.DEFAULT_QUALITY
        
        original_size = len(image_bytes)
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            original_dimensions = img.size
            original_format = img.format
            
            # Convert to RGB if saving as JPEG
            if format.upper() == 'JPEG':
                img = cls._convert_to_rgb(img)
            
            # Resize if larger than max_size (maintains aspect ratio)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_dimensions} to {img.size}")
            
            # Auto-rotate based on EXIF orientation
            try:
                from PIL import ExifTags
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = img._getexif()
                if exif:
                    orientation_value = exif.get(orientation)
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                pass  # No EXIF data
            
            # Compress
            output = io.BytesIO()
            save_kwargs = {
                'format': format.upper(),
                'optimize': True
            }
            
            if format.upper() in ('JPEG', 'WEBP'):
                save_kwargs['quality'] = quality
            elif format.upper() == 'PNG':
                save_kwargs['compress_level'] = 6
            
            img.save(output, **save_kwargs)
            optimized_bytes = output.getvalue()
            
            optimized_size = len(optimized_bytes)
            compression_ratio = round((1 - optimized_size / original_size) * 100, 2)
            
            metadata = {
                'original_size_kb': round(original_size / 1024, 2),
                'optimized_size_kb': round(optimized_size / 1024, 2),
                'compression_ratio': compression_ratio,
                'original_dimensions': original_dimensions,
                'optimized_dimensions': img.size,
                'original_format': original_format,
                'output_format': format.upper()
            }
            
            logger.info(
                f"Image optimized: {metadata['original_size_kb']}KB → "
                f"{metadata['optimized_size_kb']}KB ({compression_ratio}% reduction)"
            )
            
            return optimized_bytes, metadata
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            # Return original bytes if optimization fails
            return image_bytes, {'error': str(e), 'original_size_kb': round(original_size / 1024, 2)}
    
    @classmethod
    def create_thumbnail(
        cls,
        image_bytes: bytes,
        size: Tuple[int, int] = None,
        format: str = 'JPEG'
    ) -> Optional[bytes]:
        """
        Create a thumbnail from an image
        
        Args:
            image_bytes: Raw image bytes
            size: Thumbnail dimensions (width, height)
            format: Output format
        
        Returns:
            Thumbnail bytes or None on failure
        """
        size = size or cls.DEFAULT_THUMBNAIL_SIZE
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert mode if needed
            if format.upper() == 'JPEG':
                img = cls._convert_to_rgb(img)
            
            # Create thumbnail (maintains aspect ratio)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            save_kwargs = {
                'format': format.upper(),
                'optimize': True
            }
            
            if format.upper() in ('JPEG', 'WEBP'):
                save_kwargs['quality'] = cls.THUMBNAIL_QUALITY
            
            img.save(output, **save_kwargs)
            
            thumbnail_bytes = output.getvalue()
            logger.debug(
                f"Thumbnail created: {size[0]}x{size[1]}, "
                f"{round(len(thumbnail_bytes) / 1024, 2)}KB"
            )
            
            return thumbnail_bytes
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            return None
    
    @classmethod
    def get_image_info(cls, image_bytes: bytes) -> dict:
        """
        Get information about an image without modifying it
        
        Args:
            image_bytes: Raw image bytes
        
        Returns:
            Dictionary with image information
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return {
                'format': img.format,
                'mode': img.mode,
                'width': img.size[0],
                'height': img.size[1],
                'size_kb': round(len(image_bytes) / 1024, 2),
                'has_transparency': img.mode in ('RGBA', 'LA', 'P')
            }
        except Exception as e:
            return {'error': str(e)}
    
    @classmethod
    def convert_to_webp(
        cls,
        image_bytes: bytes,
        quality: int = 85
    ) -> Tuple[bytes, dict]:
        """
        Convert image to WebP format for better compression
        
        Args:
            image_bytes: Raw image bytes
            quality: WebP quality (1-100)
        
        Returns:
            Tuple of (webp_bytes, metadata_dict)
        """
        return cls.optimize_image(
            image_bytes,
            max_size=cls.DEFAULT_MAX_SIZE,
            quality=quality,
            format='WEBP'
        )


# Global optimizer instance
optimizer = ImageOptimizer()
