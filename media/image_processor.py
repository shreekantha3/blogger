"""
Image Processor for Media Engine.

ARCHITECTURAL DECISION: Facade Pattern for Image Processing
-----------------------------------------------------------
ImageProcessor provides a simplified interface for:
1. Image compression with quality settings
2. WebP format conversion
3. Auto-format selection based on browser support
4. Batch processing capabilities

Follows the facade pattern - delegates to Pillow library for actual processing.
"""

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from config import get_logger

logger = get_logger("media", "image_processor")


@dataclass
class ImageOptimizationConfig:
    """
    Configuration for image optimization.

    Attributes:
        quality: JPEG/WebP quality (1-100)
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        format: Target format (jpeg, webp, png, auto)
        optimize: Enable additional optimization
        progressive: Enable progressive JPEG (smaller file, slower decode)
    """

    quality: int = 85
    max_width: int = 1200
    max_height: int = 630
    format: str = "auto"
    optimize: bool = True
    progressive: bool = True


class ImageProcessor:
    """
    Process and optimize images for web publishing.

    Handles compression, format conversion, and resizing for:
    - Blog post images
    - Open Graph thumbnails (1200x630)
    - General image optimization
    """

    def __init__(self, config: Optional[ImageOptimizationConfig] = None) -> None:
        """
        Initialize image processor.

        Args:
            config: Optional optimization configuration
        """
        self.config = config or ImageOptimizationConfig()

        if not PIL_AVAILABLE:
            logger.warning("Pillow not installed - image processing will be limited")

    def optimize_image(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        config: Optional[ImageOptimizationConfig] = None,
    ) -> bytes:
        """
        Optimize an image file for web publishing.

        Args:
            image_path: Path to source image
            output_path: Optional path to save optimized image
            config: Optional config override

        Returns:
            Optimized image as bytes

        Raises:
            ImportError: If Pillow is not installed
            ValueError: If image format is not supported

        Example:
            >>> processor = ImageProcessor()
            >>> optimized = processor.optimize_image(Path("input.jpg"), Path("output.webp"))
        """
        cfg = config or self.config

        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow is required for image processing. "
                "Install with: pip install pillow"
            )

        logger.info("Optimizing image", path=str(image_path))

        # Load image
        image = Image.open(image_path)

        # Convert to RGB if necessary (for JPEG/WebP)
        if image.mode in ("RGBA", "LA", "P"):
            # Create white background for transparent images
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            if image.mode in ("RGBA", "LA"):
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
            image = background

        # Resize if needed while maintaining aspect ratio
        if image.width > cfg.max_width or image.height > cfg.max_height:
            image = self._resize_maintain_aspect(image, cfg.max_width, cfg.max_height)

        # Determine output format
        output_format = self._determine_format(image_path, cfg.format)

        # Optimize and save
        output = io.BytesIO()
        save_kwargs = {"format": output_format}

        if output_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = cfg.quality
            if output_format == "JPEG":
                save_kwargs["progressive"] = cfg.progressive
            save_kwargs["optimize"] = cfg.optimize

        image.save(output, **save_kwargs)
        optimized_bytes = output.getvalue()

        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(optimized_bytes)
            logger.info("Saved optimized image", path=str(output_path))

        logger.info(
            "Image optimized",
            original_size=image_path.stat().st_size,
            optimized_size=len(optimized_bytes),
            format=output_format,
        )

        return optimized_bytes

    def create_webp(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        quality: int = 85,
    ) -> bytes:
        """
        Convert an image to WebP format.

        Args:
            image_path: Path to source image
            output_path: Optional path to save WebP image
            quality: WebP quality (1-100)

        Returns:
            WebP image as bytes

        Example:
            >>> processor = ImageProcessor()
            >>> webp_bytes = processor.create_webp(Path("photo.jpg"))
        """
        if not PIL_AVAILABLE:
            raise ImportError("Pillow is required for WebP conversion")

        image = Image.open(image_path)

        # Convert to RGB if necessary
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            if image.mode in ("RGBA", "LA"):
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
            image = background

        output = io.BytesIO()
        image.save(output, format="WEBP", quality=quality, optimize=True)
        webp_bytes = output.getvalue()

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(webp_bytes)

        return webp_bytes

    def resize_to_dimensions(
        self,
        image_path: Path,
        width: int,
        height: int,
        output_path: Optional[Path] = None,
        maintain_aspect: bool = True,
    ) -> bytes:
        """
        Resize image to specific dimensions.

        Args:
            image_path: Path to source image
            width: Target width in pixels
            height: Target height in pixels
            output_path: Optional path to save resized image
            maintain_aspect: Whether to maintain aspect ratio

        Returns:
            Resized image as bytes

        Example:
            >>> processor = ImageProcessor()
            >>> thumbed = processor.resize_to_dimensions(Path("img.jpg"), 1200, 630)
        """
        if not PIL_AVAILABLE:
            raise ImportError("Pillow is required for resizing")

        image = Image.open(image_path)

        if maintain_aspect:
            image = self._resize_maintain_aspect(image, width, height)
        else:
            image = image.resize((width, height), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        image.save(output, format=image.format or "JPEG", quality=self.config.quality)
        resized_bytes = output.getvalue()

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(resized_bytes)

        return resized_bytes

    def optimize_batch(
        self,
        image_paths: List[Path],
        output_dir: Optional[Path] = None,
    ) -> List[bytes]:
        """
        Optimize multiple images in batch.

        Args:
            image_paths: List of image file paths
            output_dir: Optional directory to save optimized images

        Returns:
            List of optimized image bytes

        Example:
            >>> processor = ImageProcessor()
            >>> results = processor.optimize_batch([Path("a.jpg"), Path("b.png")])
        """
        optimized = []
        for path in image_paths:
            output_path = None
            if output_dir:
                output_path = output_dir / f"{path.stem}_optimized{path.suffix}"
            result = self.optimize_image(path, output_path)
            optimized.append(result)

        return optimized

    def get_image_info(self, image_path: Path) -> dict:
        """
        Get image metadata without optimization.

        Args:
            image_path: Path to image file

        Returns:
            Dict with width, height, format, mode, and file_size

        Example:
            >>> info = processor.get_image_info(Path("photo.jpg"))
            >>> print(info["width"], info["height"])
        """
        if not PIL_AVAILABLE:
            raise ImportError("Pillow is required for image info")

        image = Image.open(image_path)
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "file_size": image_path.stat().st_size,
        }

    def _resize_maintain_aspect(
        self,
        image: "Image.Image",
        max_width: int,
        max_height: int,
    ) -> "Image.Image":
        """
        Resize image maintaining aspect ratio.

        Args:
            image: PIL Image object
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Resized PIL Image
        """
        import math

        ratio = min(max_width / image.width, max_height / image.height)

        if ratio >= 1:
            return image  # No resize needed

        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _determine_format(self, image_path: Path, format_setting: str) -> str:
        """
        Determine output format based on settings and input.

        Args:
            image_path: Source image path
            format_setting: Format setting (jpeg, webp, png, auto)

        Returns:
            Output format string for PIL
        """
        if format_setting == "auto":
            # Default to WebP for best compression
            return "WEBP"

        format_map = {
            "jpeg": "JPEG",
            "jpg": "JPEG",
            "webp": "WEBP",
            "png": "PNG",
        }

        return format_map.get(format_setting.lower(), "JPEG")