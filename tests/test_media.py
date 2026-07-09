"""
Tests for Media Engine (Phase 5).

These tests cover:
- Image processing and optimization
- Thumbnail generation
- Storage backends
- Image selection and alt text
"""

import io
from pathlib import Path

import pytest

# Skip all tests if Pillow is not available
pytest.importorskip("PIL", reason="Pillow required for media tests")


class TestImageProcessor:
    """Tests for ImageProcessor class."""

    def test_optimize_image_returns_bytes(self, tmp_path: Path) -> None:
        """optimize_image should return image bytes."""
        from media.image_processor import ImageProcessor, ImageOptimizationConfig

        processor = ImageProcessor()

        # Create a test image
        from PIL import Image
        test_img = Image.new("RGB", (800, 600), color="red")
        input_path = tmp_path / "input.jpg"
        test_img.save(input_path, "JPEG")

        result = processor.optimize_image(input_path)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_optimize_image_resizes_large_images(self, tmp_path: Path) -> None:
        """Large images should be resized to max dimensions."""
        from media.image_processor import ImageProcessor, ImageOptimizationConfig

        config = ImageOptimizationConfig(max_width=400, max_height=300)
        processor = ImageProcessor(config)

        # Create a large test image
        from PIL import Image
        test_img = Image.new("RGB", (2000, 1500), color="blue")
        input_path = tmp_path / "large.jpg"
        test_img.save(input_path, "JPEG")

        result = processor.optimize_image(input_path)

        # Check output size is reasonable
        output_img = Image.open(io.BytesIO(result))
        assert output_img.width <= 400
        assert output_img.height <= 300

    def test_get_image_info(self, tmp_path: Path) -> None:
        """get_image_info should return metadata."""
        from media.image_processor import ImageProcessor

        processor = ImageProcessor()

        from PIL import Image
        test_img = Image.new("RGB", (500, 400), color="green")
        input_path = tmp_path / "test.jpg"
        test_img.save(input_path, "JPEG")

        info = processor.get_image_info(input_path)

        assert info["width"] == 500
        assert info["height"] == 400
        assert info["format"] == "JPEG"
        assert info["mode"] == "RGB"

    def test_webp_conversion(self, tmp_path: Path) -> None:
        """create_webp should convert to WebP format."""
        from media.image_processor import ImageProcessor

        processor = ImageProcessor()

        from PIL import Image
        test_img = Image.new("RGB", (400, 300), color="blue")
        input_path = tmp_path / "test.jpg"
        test_img.save(input_path, "JPEG")

        webp_bytes = processor.create_webp(input_path)

        assert isinstance(webp_bytes, bytes)
        # Verify it's WebP by loading it
        from PIL import Image
        img = Image.open(io.BytesIO(webp_bytes))
        assert img.format == "WEBP"


class TestThumbnailGenerator:
    """Tests for ThumbnailGenerator class."""

    def test_generate_og_thumbnail(self, tmp_path: Path) -> None:
        """generate_og_thumbnail should create 1200x630 image."""
        from media.thumbnail_generator import ThumbnailGenerator

        generator = ThumbnailGenerator()
        output_path = tmp_path / "thumb.jpg"

        result = generator.generate_og_thumbnail("Test Article", output_path)

        assert isinstance(result, bytes)
        assert output_path.exists()

        # Verify dimensions
        from PIL import Image
        img = Image.open(output_path)
        assert img.width == 1200
        assert img.height == 630

    def test_generate_twitter_thumbnail(self, tmp_path: Path) -> None:
        """generate_twitter_thumbnail should create 1200x600 image."""
        from media.thumbnail_generator import ThumbnailGenerator

        generator = ThumbnailGenerator()

        result = generator.generate_twitter_thumbnail("Python Tips")

        assert isinstance(result, bytes)
        from PIL import Image
        img = Image.open(io.BytesIO(result))
        assert img.width == 1200
        assert img.height == 600

    def test_generate_square_thumbnail(self, tmp_path: Path) -> None:
        """generate_square_thumbnail should create square image."""
        from media.thumbnail_generator import ThumbnailGenerator

        generator = ThumbnailGenerator()

        result = generator.generate_square_thumbnail("Test Title")

        assert isinstance(result, bytes)
        from PIL import Image
        img = Image.open(io.BytesIO(result))
        assert img.width == 1080
        assert img.height == 1080

    def test_thumbnail_text_overflow(self) -> None:
        """Very long titles should be wrapped."""
        from media.thumbnail_generator import ThumbnailGenerator, ThumbnailConfig

        generator = ThumbnailGenerator()

        # Very long title
        long_title = "This is an extremely long article title that should definitely wrap to multiple lines in the thumbnail"

        result = generator.generate_from_template(long_title)

        assert isinstance(result, bytes)
        # Should still produce valid image
        from PIL import Image
        img = Image.open(io.BytesIO(result))
        assert img.width > 0


class TestLocalStorage:
    """Tests for LocalStorage backend."""

    def test_upload_and_retrieve(self, tmp_path: Path) -> None:
        """upload should save file and get_url should return URL."""
        from media.storage import LocalStorage, StorageConfig

        storage = LocalStorage(tmp_path, "https://example.com/images")

        result_url = storage.upload(b"test image data", "test.jpg")

        assert result_url == "https://example.com/images/test.jpg"
        assert (tmp_path / "test.jpg").exists()

    def test_upload_file(self, tmp_path: Path) -> None:
        """upload_file should copy file to storage."""
        from media.storage import LocalStorage

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "source.jpg"
        source_file.write_bytes(b"test data")

        storage_dir = tmp_path / "storage"
        storage = LocalStorage(storage_dir, "https://cdn.example.com")

        result_url = storage.upload_file(source_file)

        assert result_url == "https://cdn.example.com/source.jpg"

    def test_delete(self, tmp_path: Path) -> None:
        """delete should remove file from storage."""
        from media.storage import LocalStorage

        storage = LocalStorage(tmp_path, "https://example.com")
        storage.upload(b"data", "to_delete.jpg")

        result = storage.delete("to_delete.jpg")

        assert result is True
        assert not (tmp_path / "to_delete.jpg").exists()


class TestStorageConfig:
    """Tests for StorageConfig dataclass."""

    def test_default_config(self) -> None:
        """Default config should have sensible values."""
        from media.storage import StorageConfig

        config = StorageConfig()

        assert config.provider == "local"
        assert config.bucket_name is None
        assert config.region is None


class TestImageSelector:
    """Tests for ImageSelector class."""

    def test_suggest_images_returns_list(self) -> None:
        """suggest_images should return ImageSuggestion objects."""
        from media.image_selector import ImageSelector

        selector = ImageSelector()

        suggestions = selector.suggest_images(
            topic="Python programming",
            count=4,
        )

        assert len(suggestions) == 4
        for suggestion in suggestions:
            assert hasattr(suggestion, "url")
            assert hasattr(suggestion, "alt_text")
            assert hasattr(suggestion, "to_html")

    def test_suggest_images_with_headings(self) -> None:
        """suggest_images should use headings for context."""
        from media.image_selector import ImageSelector

        selector = ImageSelector()

        suggestions = selector.suggest_images(
            topic="Python",
            headings=["Introduction", "Basics", "Advanced"],
            count=3,
        )

        assert len(suggestions) == 3
        # Alt text should include heading context
        for suggestion in suggestions:
            assert len(suggestion.alt_text) > 0

    def test_generate_alt_text_fallback(self) -> None:
        """generate_alt_text should work without AI provider."""
        from media.image_selector import ImageSelector

        selector = ImageSelector()

        alt = selector.generate_alt_text("Python code example")

        assert isinstance(alt, str)
        assert len(alt) <= 125
        assert "Python" in alt

    def test_to_html_generation(self) -> None:
        """ImageSuggestion.to_html should produce valid HTML."""
        from media.image_selector import ImageSuggestion

        suggestion = ImageSuggestion(
            url="https://example.com/img.jpg",
            alt_text="Test image",
        )

        html = suggestion.to_html()

        assert '<img src="https://example.com/img.jpg"' in html
        assert 'alt="Test image"' in html
        assert 'loading="lazy"' in html

    def test_validate_image_seo(self) -> None:
        """validate_image_for_seo should check alt text requirements."""
        from media.image_selector import ImageSelector

        selector = ImageSelector()

        result = selector.validate_image_for_seo(
            image_url="https://example.com/img.jpg",
            alt_text="Python programming illustration showing code examples and concepts",
            topic="Python programming",
        )

        assert "is_valid" in result
        assert "alt_text_length" in result
        assert "issues" in result
        assert "recommendations" in result


class TestQualityScorer:
    """Tests for QualityScorer (EEAT)."""

    def test_score_content_returns_score(self) -> None:
        """score_content should return QualityScore with breakdown."""
        from seo.quality_scorer import QualityScorer

        scorer = QualityScorer()

        content = """
        <h1>Python Programming Guide</h1>
        <p>In my experience, Python is widely used.
        According to research, it has many benefits.</p>
        <p>Source: Python.org documentation</p>
        """

        score = scorer.score_content("Python Guide", content)

        assert score.overall >= 0
        assert score.overall <= 100
        assert score.experience >= 0
        assert score.expertise >= 0
        assert score.authoritativeness >= 0
        assert score.trustworthiness >= 0

    def test_eeat_report_generation(self) -> None:
        """generate_eeat_report should produce grade and suggestions."""
        from seo.quality_scorer import QualityScorer

        scorer = QualityScorer()

        content = "<h1>Guide</h1><p>Content with sources and research.</p>"

        report = scorer.generate_eeat_report("Guide", content)

        assert "overall_score" in report
        assert "grade" in report
        assert "breakdown" in report
        assert "issues" in report
        assert "suggestions" in report

    def test_content_with_experience_indicators(self) -> None:
        """Content with experience language should score higher on experience."""
        from seo.quality_scorer import QualityScorer

        scorer = QualityScorer()

        content = "<p>In my experience, this works well. We found great results.</p>"
        score = scorer.score_content("Experience", content)

        # Should have higher experience score due to indicators
        assert score.experience > 50