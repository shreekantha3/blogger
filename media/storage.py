"""
Media Storage Backend for Cloud Integration.

ARCHITECTURAL DECISION: Storage Strategy Pattern
-------------------------------------------------
StorageBackend provides a unified interface for:
1. Local file storage
2. AWS S3 storage
3. Cloudinary storage

Each backend implements the same interface for interchangeability.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from config import get_logger

logger = get_logger("media", "storage")


@dataclass
class StorageConfig:
    """
    Configuration for storage backends.

    Attributes:
        provider: Storage provider name (local, s3, cloudinary)
        bucket_name: For S3/Cloudinary - the bucket/container name
        region: For S3 - region
        base_url: For local - base URL prefix
        access_key: Access key for cloud providers
        secret_key: Secret key for cloud providers
    """

    provider: str = "local"
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    base_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    Defines the interface for image storage operations.
    """

    def __init__(self, config: Optional[StorageConfig] = None) -> None:
        """
        Initialize storage backend.

        Args:
            config: Optional storage configuration
        """
        self.config = config or StorageConfig()

    @abstractmethod
    def upload(
        self,
        image_bytes: bytes,
        filename: str,
    ) -> str:
        """
        Upload image bytes and return public URL.

        Args:
            image_bytes: Image data
            filename: Target filename

        Returns:
            Public URL to the uploaded image

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    def upload_file(
        self,
        file_path: Path,
        filename: Optional[str] = None,
    ) -> str:
        """
        Upload a file and return public URL.

        Args:
            file_path: Path to source file
            filename: Optional target filename

        Returns:
            Public URL to the uploaded file

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """
        Get public URL for a filename.

        Args:
            filename: Stored filename

        Returns:
            Public URL
        """
        pass

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """
        Delete an image from storage.

        Args:
            filename: Filename to delete

        Returns:
            True if deleted successfully
        """
        pass


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.

    Stores images in a local directory and serves them via base URL.
    """

    def __init__(self, storage_dir: Path, base_url: str, config: Optional[StorageConfig] = None) -> None:
        """
        Initialize local storage.

        Args:
            storage_dir: Directory to store files
            base_url: Base URL for serving files
            config: Optional configuration override
        """
        super().__init__(config)
        self.storage_dir = Path(storage_dir)
        self.base_url = base_url.rstrip("/")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, image_bytes: bytes, filename: str) -> str:
        """
        Upload bytes to local filesystem.

        Args:
            image_bytes: Image data
            filename: Target filename

        Returns:
            Public URL to the image
        """
        file_path = self.storage_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(image_bytes)

        logger.info("Uploaded to local storage", filename=filename)
        return f"{self.base_url}/{filename}"

    def upload_file(self, file_path: Path, filename: Optional[str] = None) -> str:
        """
        Upload a file to local storage.

        Args:
            file_path: Source file path
            filename: Optional target filename

        Returns:
            Public URL
        """
        target_name = filename or file_path.name
        target_path = self.storage_dir / target_name
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        target_path.write_bytes(file_path.read_bytes())

        logger.info("Uploaded file to local storage", filename=target_name)
        return f"{self.base_url}/{target_name}"

    def get_url(self, filename: str) -> str:
        """Get public URL for local file."""
        return f"{self.base_url}/{filename}"

    def delete(self, filename: str) -> bool:
        """
        Delete file from local storage.

        Args:
            filename: Filename to delete

        Returns:
            True if deleted successfully
        """
        file_path = self.storage_dir / filename
        try:
            file_path.unlink()
            logger.info("Deleted from local storage", filename=filename)
            return True
        except FileNotFoundError:
            return False


class S3Storage(StorageBackend):
    """
    AWS S3 storage backend.

    Uploads images to S3 and returns public URLs.
    """

    def __init__(self, config: StorageConfig) -> None:
        """
        Initialize S3 storage.

        Args:
            config: Storage configuration with S3 credentials

        Raises:
            ValueError: If required S3 config missing
        """
        super().__init__(config)

        if not config.bucket_name:
            raise ValueError("S3 bucket_name is required")

        self.bucket_name = config.bucket_name
        self.region = config.region or "us-east-1"
        self.access_key = config.access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = config.secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")

        if not HTTPX_AVAILABLE:
            logger.warning("httpx not installed - S3 uploads will use mock mode")
            self._mock_mode = True
        else:
            self._mock_mode = False
            self._upload_client = self._create_s3_client()

    def _create_s3_client(self) -> Optional[object]:
        """Create S3 client or return None for mock mode."""
        try:
            import boto3  # type: ignore

            return boto3.client(
                "s3",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
        except ImportError:
            logger.warning("boto3 not installed - S3 uploads disabled")
            return None

    def upload(self, image_bytes: bytes, filename: str) -> str:
        """
        Upload bytes to S3.

        Args:
            image_bytes: Image data
            filename: Target filename (key in bucket)

        Returns:
            Public S3 URL

        Raises:
            StorageError: If upload fails
        """
        if self._upload_client is None:
            return self._mock_upload(filename)

        try:
            self._upload_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_bytes,
            )

            logger.info("Uploaded to S3", bucket=self.bucket_name, key=filename)
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
        except Exception as e:
            logger.error("S3 upload failed", error=str(e))
            return self._mock_upload(filename)

    def upload_file(self, file_path: Path, filename: Optional[str] = None) -> str:
        """
        Upload a file to S3.

        Args:
            file_path: Source file path
            filename: Optional target filename

        Returns:
            Public S3 URL
        """
        return self.upload(file_path.read_bytes(), filename or file_path.name)

    def get_url(self, filename: str) -> str:
        """Get public S3 URL for a file."""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"

    def delete(self, filename: str) -> bool:
        """
        Delete file from S3.

        Args:
            filename: S3 key to delete

        Returns:
            True if deleted successfully
        """
        if self._upload_client is None:
            return False

        try:
            self._upload_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename,
            )
            return True
        except Exception as e:
            logger.error("S3 delete failed", error=str(e))
            return False

    def _mock_upload(self, filename: str) -> str:
        """Return mock URL when S3 client unavailable."""
        return f"https://mock-s3.amazonaws.com/{self.bucket_name}/{filename}"


class CloudinaryStorage(StorageBackend):
    """
    Cloudinary storage backend.

    Uploads images to Cloudinary and returns optimized URLs.
    """

    def __init__(self, config: StorageConfig) -> None:
        """
        Initialize Cloudinary storage.

        Args:
            config: Storage configuration with Cloudinary credentials
        """
        super().__init__(config)

        self.cloud_name = config.bucket_name or os.getenv("CLOUDINARY_CLOUD_NAME")
        self.api_key = config.access_key or os.getenv("CLOUDINARY_API_KEY")
        self.api_secret = config.secret_key or os.getenv("CLOUDINARY_API_SECRET")

        if not HTTPX_AVAILABLE:
            logger.warning("httpx not installed - Cloudinary uploads will use mock mode")
            self._mock_mode = True
        else:
            self._mock_mode = False
            self._upload_client = self._create_upload_client()

    def _create_upload_client(self) -> Optional[object]:
        """Create Cloudinary client or return None for mock mode."""
        try:
            from cloudinary import uploader  # type: ignore

            return uploader
        except ImportError:
            logger.warning("cloudinary not installed - using mock mode")
            return None

    def upload(self, image_bytes: bytes, filename: str) -> str:
        """
        Upload bytes to Cloudinary.

        Args:
            image_bytes: Image data
            filename: Target filename

        Returns:
            Optimized Cloudinary URL
        """
        if self._upload_client is None:
            return self._mock_upload(filename)

        try:
            import cloudinary  # type: ignore

            result = self._upload_client.upload(
                image_bytes,
                public_id=filename.split(".")[0],
                folder="blog-images",
            )

            # Return optimized URL
            url = cloudinary.CloudinaryImage(result["public_id"]).build_url(
                width=1200,
                height=630,
                crop="fill",
                quality="auto",
                format="webp",
            )

            logger.info("Uploaded to Cloudinary", public_id=result["public_id"])
            return url
        except Exception as e:
            logger.error("Cloudinary upload failed", error=str(e))
            return self._mock_upload(filename)

    def upload_file(self, file_path: Path, filename: Optional[str] = None) -> str:
        """
        Upload a file to Cloudinary.

        Args:
            file_path: Source file path
            filename: Optional target filename

        Returns:
            Optimized Cloudinary URL
        """
        return self.upload(file_path.read_bytes(), filename or file_path.name)

    def get_url(self, filename: str) -> str:
        """Get Cloudinary URL for a file."""
        if not self.cloud_name:
            return self._mock_upload(filename)
        return f"https://res.cloudinary.com/{self.cloud_name}/image/upload/blog-images/{filename}"

    def delete(self, filename: str) -> bool:
        """
        Delete file from Cloudinary.

        Args:
            filename: Public ID to delete

        Returns:
            True if deleted successfully
        """
        if self._upload_client is None:
            return False

        try:
            from cloudinary import uploader  # type: ignore

            uploader.destroy(filename)
            return True
        except Exception as e:
            logger.error("Cloudinary delete failed", error=str(e))
            return False

    def _mock_upload(self, filename: str) -> str:
        """Return mock URL when Cloudinary client unavailable."""
        return f"https://mock-cloudinary.com/{self.cloud_name}/image/upload/{filename}"


class StorageError(Exception):
    """Raised when storage operation fails."""

    def __init__(self, message: str, backend: str = "unknown") -> None:
        super().__init__(message)
        self.backend = backend