"""
Thumbnail Generator for Social Media Sharing.

ARCHITECTURAL DECISION: Thumbnail Generation Service
----------------------------------------------------
ThumbnailGenerator provides automatic generation of:
1. Open Graph thumbnails (1200x630px) - Facebook, LinkedIn, etc.
2. Twitter Card images (1200x600px)
3. Square thumbnails (1080x1080px) - Instagram
4. Small thumbnails (600x315px) - Generic social

Uses Pillow for image processing with text overlay support.
"""

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from config import get_logger

logger = get_logger("media", "thumbnail_generator")


@dataclass
class ThumbnailConfig:
    """
    Configuration for thumbnail generation.

    Attributes:
        width: Thumbnail width in pixels
        height: Thumbnail height in pixels
        background_color: Background color (hex or RGB tuple)
        text_color: Text color for overlay
        font_size: Font size for title text
        margin: Margin around text
    """

    width: int = 1200
    height: int = 630
    background_color: Tuple[int, int, int] = (45, 55, 72)  # Dark blue
    text_color: Tuple[int, int, int] = (255, 255, 255)  # White
    font_size: int = 64
    margin: int = 80


class ThumbnailGenerator:
    """
    Generate social media thumbnails with text overlay.

    Creates Open Graph optimized images with:
    - 1200x630px dimensions (standard)
    - Proper aspect ratio (1.91:1)
    - Text overlay support for branding
    - Multiple format support (JPEG, WebP)
    """

    # Standard thumbnail dimensions
    OG_STANDARD = (1200, 630)  # Open Graph (1.91:1)
    TWITTER_LARGE = (1200, 600)  # Twitter Card
    INSTAGRAM_SQUARE = (1080, 1080)  # Instagram (1:1)
    GENERIC = (600, 315)  # Generic social (1.91:1)

    def __init__(self, config: Optional[ThumbnailConfig] = None) -> None:
        """
        Initialize thumbnail generator.

        Args:
            config: Optional thumbnail configuration
        """
        self.config = config or ThumbnailConfig()

        if not PIL_AVAILABLE:
            logger.warning("Pillow not installed - thumbnail generation limited")

    def generate_from_template(
        self,
        title: str,
        output_path: Optional[Path] = None,
        config: Optional[ThumbnailConfig] = None,
        background_image: Optional[Path] = None,
    ) -> bytes:
        """
        Generate thumbnail with title overlay.

        Args:
            title: Text to display on thumbnail
            output_path: Optional path to save thumbnail
            config: Optional config override
            background_image: Optional background image path

        Returns:
            Thumbnail image as bytes

        Example:
            >>> generator = ThumbnailGenerator()
            >>> thumb = generator.generate_from_template("Python Guide", Path("thumb.jpg"))
        """
        cfg = config or self.config

        if not PIL_AVAILABLE:
            raise ImportError("Pillow is required for thumbnail generation")

        logger.info("Generating thumbnail", title=title[:50])

        # Create base image
        if background_image:
            image = self._create_with_background(background_image, title, cfg)
        else:
            image = self._create_solid_background(title, cfg)

        # Convert to bytes
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=90, optimize=True)
        thumbnail_bytes = output.getvalue()

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(thumbnail_bytes)
            logger.info("Saved thumbnail", path=str(output_path))

        return thumbnail_bytes

    def generate_from_image(
        self,
        image_path: Path,
        title: str,
        output_path: Optional[Path] = None,
        config: Optional[ThumbnailConfig] = None,
    ) -> bytes:
        """
        Generate thumbnail by overlaying title on existing image.

        Args:
            image_path: Source image path
            title: Text overlay
            output_path: Optional output path
            config: Optional config override

        Returns:
            Thumbnail as bytes

        Example:
            >>> thumb = generator.generate_from_image(
            ...     Path("background.jpg"),
            ...     "My Article Title"
            ... )
        """
        cfg = config or self.config

        if not PIL_AVAILABLE:
            raise ImportError("Pillow is required for thumbnail generation")

        # Load and resize image
        image = Image.open(image_path)
        image = image.resize((cfg.width, cfg.height), Image.Resampling.LANCZOS)

        # Add text overlay
        image = self._add_text_overlay(image, title, cfg)

        # Save
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=90, optimize=True)
        thumbnail_bytes = output.getvalue()

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(thumbnail_bytes)

        return thumbnail_bytes

    def generate_og_thumbnail(
        self,
        title: str,
        output_path: Optional[Path] = None,
        background_image: Optional[Path] = None,
    ) -> bytes:
        """
        Generate Open Graph optimized thumbnail (1200x630).

        Args:
            title: Article title for overlay
            output_path: Optional output path
            background_image: Optional background image

        Returns:
            OG thumbnail as bytes

        Example:
            >>> thumb = generator.generate_og_thumbnail("Python Tips", Path("og.jpg"))
        """
        config = ThumbnailConfig(
            width=1200,
            height=630,
        )
        return self.generate_from_template(
            title, output_path, config, background_image
        )

    def generate_twitter_thumbnail(
        self,
        title: str,
        output_path: Optional[Path] = None,
    ) -> bytes:
        """
        Generate Twitter Card optimized thumbnail (1200x600).

        Args:
            title: Article title
            output_path: Optional output path

        Returns:
            Twitter thumbnail as bytes
        """
        config = ThumbnailConfig(
            width=1200,
            height=600,
        )
        return self.generate_from_template(title, output_path, config)

    def generate_square_thumbnail(
        self,
        title: str,
        output_path: Optional[Path] = None,
    ) -> bytes:
        """
        Generate Instagram-style square thumbnail (1080x1080).

        Args:
            title: Article title
            output_path: Optional output path

        Returns:
            Square thumbnail as bytes
        """
        config = ThumbnailConfig(
            width=1080,
            height=1080,
            font_size=48,
        )
        return self.generate_from_template(title, output_path, config)

    def _create_solid_background(
        self,
        title: str,
        config: ThumbnailConfig,
    ) -> "Image.Image":
        """
        Create thumbnail with solid background color.

        Args:
            title: Text to overlay
            config: Thumbnail configuration

        Returns:
            PIL Image with text overlay
        """
        image = Image.new("RGB", (config.width, config.height), config.background_color)
        return self._add_text_overlay(image, title, config)

    def _create_with_background(
        self,
        image_path: Path,
        title: str,
        config: ThumbnailConfig,
    ) -> "Image.Image":
        """
        Create thumbnail with background image.

        Args:
            image_path: Background image path
            title: Text to overlay
            config: Thumbnail configuration

        Returns:
            PIL Image with background and text
        """
        background = Image.open(image_path)
        background = background.resize(
            (config.width, config.height), Image.Resampling.LANCZOS
        )

        # Add semi-transparent overlay for text readability
        overlay = Image.new("RGBA", background.size, (0, 0, 0, 128))
        background = background.convert("RGBA")
        background.paste(overlay, mask=overlay)

        return self._add_text_overlay(background.convert("RGB"), title, config)

    def _add_text_overlay(
        self,
        image: "Image.Image",
        title: str,
        config: ThumbnailConfig,
    ) -> "Image.Image":
        """
        Add text overlay to image.

        Args:
            image: PIL Image
            title: Text to add
            config: Configuration

        Returns:
            Image with text overlay
        """
        draw = ImageDraw.Draw(image)

        # Try to load a font, fall back to default
        try:
            # On macOS, try system fonts
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", config.font_size)
        except Exception:
            try:
                font = ImageFont.load_default()
            except Exception:
                pass

        # Wrap text to fit
        lines = self._wrap_text(title, config, draw)

        # Calculate text position (centered)
        total_height = sum(
            draw.textlength(line, font=font) if hasattr(draw, 'textlength')
            else len(line) * config.font_size * 0.6
            for line in lines
        )
        y_position = (config.height - sum(
            draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]
            for line in lines
        )) // 2

        # Draw each line
        y = y_position
        for line in lines:
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            x = (config.width - text_width) // 2
            draw.text((x, y), line, fill=config.text_color, font=font)
            y += text_bbox[3] - text_bbox[1] + 20

        return image

    def _wrap_text(
        self,
        text: str,
        config: ThumbnailConfig,
        draw: "ImageDraw.ImageDraw",
    ) -> list:
        """
        Wrap text to fit within thumbnail width.

        Args:
            text: Text to wrap
            config: Configuration
            draw: ImageDraw object

        Returns:
            List of wrapped text lines
        """
        words = text.split()
        lines = []
        current_line = []

        max_width = config.width - (config.margin * 2)
        font = None

        for word in words:
            test_line = " ".join(current_line + [word])
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except Exception:
                line_width = len(test_line) * config.font_size * 0.6

            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        # Limit to reasonable number of lines
        return lines[:4]