import logging
import base64
from injector import inject, singleton
from langchain_emoji.settings.settings import Settings
from minio import Minio
from minio.error import MinioException

logger = logging.getLogger(__name__)


@singleton
class MinioComponent:
    @inject
    def __init__(self, settings: Settings) -> None:
        if not settings.minio:
            raise Exception("minio config is not exist! please check")
        self.minio_settings = settings.minio
        self.minio_client = Minio(
            endpoint=self.minio_settings.host,
            access_key=self.minio_settings.access_key,
            secret_key=self.minio_settings.secret_key,
            secure=False,
        )

    def get_file_base64(self, file_name: str) -> str:
        try:
            response = self.minio_client.get_object(
                self.minio_settings.bucket_name, file_name
            )
            # Read the object content
            object_data = response.read()

            # Encode object data to base64
            base64_data = base64.b64encode(object_data)

            return base64_data.decode("utf-8")
        except MinioException as e:
            logger.error(f"get file base64 failed : {e}")
            return None

    def get_download_link(self, file_name: str) -> str:
        try:
            # Generate presigned URL for download
            presigned_url = self.minio_client.presigned_get_object(
                self.minio_settings.bucket_name, file_name
            )
            return presigned_url
        except MinioException as e:
            logger.error(f"get share link failed : {e}")
            return None


if __name__ == "__main__":
    from langchain_emoji.settings.settings import settings

    mc = MinioComponent(settings())

    obj = "06e07a24-df07-4781-a1da-58739ac65404.jpg"

    print(mc.get_file_base64(obj))
    print(mc.get_download_link(obj))
