import gdown
import zipfile
import os
import sys
import argparse
from tqdm import tqdm
from pathlib import Path
import hashlib
from minio import Minio
from minio.error import MinioException
from langchain_core.vectorstores import VectorStore
from langchain_emoji.components.vector_store.tencent.tencent import EmojiTencentVectorDB

import concurrent.futures
import threading
import jsonlines
from queue import Queue

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 从百度下载数据，解析
# https://pan.baidu.com/s/11iwqoxLtjV-DOQli81vZ6Q?pwd=tab4
# 下载到local_data


# 或者从谷歌云下载 (可选)
# 定义谷歌云盘文件的ID
def download_and_extract_data(file_id: str, output_dir: Path) -> bool:
    """
    Download a file from Google Drive and extract it to the specified directory.

    Parameters:
    - file_id (str): Google Drive file ID.
    - output_dir (str): Directory to extract the downloaded file.

    Returns:
    - bool: True if successful, False otherwise.
    """
    try:
        # Define Google Drive download URL
        url = f"https://drive.google.com/uc?id={file_id}"

        # Define the output file path
        output_path = str(output_dir / "emo-visual-data.zip")

        # Download the file
        gdown.download(url, output_path, quiet=False)

        # Create the extraction directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Extract the downloaded file
        with zipfile.ZipFile(output_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)

        # Clean up: remove the downloaded zip file
        os.remove(output_path)

        logger.info("File downloaded and extracted successfully.")
        return True

    except Exception as e:
        logger.exception(f"Error: {e}")
        return False


def calculate_md5(file_path: str) -> str:
    """
    Calculate the MD5 hash of a file.

    Parameters:
    - file_path (str): Path to the file.

    Returns:
    - str: MD5 hash of the file.
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # 以二进制方式读取文件内容并计算MD5值
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def create_minio_bucket(minio_client: Minio, bucket_name: str) -> bool:
    """
    Create a MinIO bucket if it doesn't already exist.

    Parameters:
    - minio_client (Minio): MinIO client object.
    - bucket_name (str): Name of the MinIO bucket to create.

    Returns:
    - bool: True if successful or the bucket already exists, False otherwise.
    """
    try:
        # Check if the bucket already exists
        if minio_client.bucket_exists(bucket_name):
            logger.info(f"Bucket '{bucket_name}' already exists.")
            return True
        else:
            # Create the bucket
            minio_client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created successfully.")
            return True

    except MinioException as err:
        logger.exception(f"MinIO error: {err}")
        return False


def upload_file(
    minio_client: Minio,
    bucket_name: str,
    file_path: str,
    object_name: str,
    file_md5: str,
    failed_files: list,
    progress_queue: Queue,
) -> bool:
    """
    Upload a single file to MinIO.

    Parameters:
     Parameters:
    - minio_client (Minio): MinIO client object.
    - bucket_name (str): Name of the MinIO bucket.
    - file_path (str): Path to the file.
    - object_name (str): Object name in MinIO.
    - file_md5 (str): MD5 hash of the file.
    - total_pbar (tqdm): Total progress bar.
    - failed_files (list): List to store failed file names.

    Returns:
    - bool: True if successful, False otherwise.
    """
    try:
        try:
            # 检查MinIO中是否已存在相同对象（文件）并且MD5值相同。
            object_stat = minio_client.stat_object(bucket_name, object_name)
            # 如果对象存在且MD5值相等，跳过此文件。'ETag': '"c204c0f5ab34d3caa8909efd81b24c47"'
            if object_stat.metadata["ETag"][1:-1] == file_md5:
                logger.debug(
                    f"Skipping {file_path}: File already exists in MinIO with same MD5."
                )
                progress_queue.put(1)
                return True
        except MinioException as e:
            # 如果对象不存在或MD5值不相等，则继续上传。
            if e.code != "NoSuchKey":
                logger.error(f"Error checking object: {e}")
                return False

        # 上传文件到MinIO。
        minio_client.fput_object(
            bucket_name,
            object_name,
            file_path,
        )
        logger.debug(f"Uploaded {file_path} to MinIO.")
        progress_queue.put(1)
        return True

    except MinioException as e:
        logger.error(f"Error uploading {file_path} to MinIO: {e}")
        failed_files.append(file_path)
        progress_queue.put(1)
        return False


def track_progress(total: int, progress_queue: Queue):
    # 创建总进度条。
    with tqdm(
        total=total,
        leave=True,
        ncols=100,
        file=sys.stdout,
        desc=f"Total Files {total}",
        unit="files",
    ) as total_pbar:

        while True:
            progress_queue.get()
            total_pbar.update(1)
            if total_pbar.n >= total_pbar.total:
                break


# 上传云端Minio（可选）
def upload_to_minio(minio_client: Minio, source_dir: Path, bucket_name: str) -> bool:
    """
    Upload files from a local directory to a MinIO bucket.

    Parameters:
    - minio_client (Minio): MinIO client object.
    - source_dir (str): Directory containing the files to upload.
    - bucket_name (str): Name of the MinIO bucket.

    Returns:
    - bool: True if successful, False otherwise.
    """

    # 保存上传失败的文件名的文件路径
    failed_files_path = "failed_files.txt"
    # 上传失败的文件列表
    failed_files = []

    if not create_minio_bucket(minio_client, bucket_name):
        return False

    try:

        # 使用线程池并发执行文件上传任务
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            progress_queue = Queue()
            total_files = sum(len(files) for _, _, files in os.walk(source_dir))
            # 遍历源目录中的所有文件。
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算对象名称（相对于source_dir的相对路径）。
                    object_name = os.path.relpath(file_path, source_dir)
                    # 计算文件的MD5值。
                    file_md5 = calculate_md5(file_path)
                    # 提交上传任务到线程池。
                    future = executor.submit(
                        upload_file,
                        minio_client,
                        bucket_name,
                        file_path,
                        object_name,
                        file_md5,
                        failed_files,
                        progress_queue,
                    )
                    futures.append(future)

            # Start the progress tracking thread
            progress_thread = threading.Thread(
                target=track_progress, args=(len(futures), progress_queue), daemon=True
            )
            progress_thread.start()

            # 等待所有上传任务完成。
            for future in concurrent.futures.as_completed(futures):
                if not future.result():
                    logger.error(f"result error:{future.result()}")

        logger.info(f"All {total_files} files uploaded to MinIO.")
        # 输出上传成功和失败文件数量
        success_count = total_files - len(failed_files)
        logger.info(f"Total files uploaded successfully: {success_count}")
        logger.info(f"Total files failed to upload: {len(failed_files)}")

        # 将上传失败的文件名保存到文件中
        if failed_files:
            with open(failed_files_path, "w") as f:
                f.write("\n".join(failed_files))

        progress_thread.join()

        return True

    except Exception as err:
        logger.exception(f"An error occurred: {err}")
        return False


# 加载向量数据库


def upload_file_vectordb(
    client: VectorStore,
    data: dict,
    failed_files: list,
    progress_queue: Queue,
) -> bool:
    try:
        filename = data["filename"]
        content = data["content"]

        if isinstance(client, EmojiTencentVectorDB):
            metadata = {
                "filename": filename,
            }

            result = client.add_original_texts_with_filename(
                filename=filename, texts=[content], metadatas=[metadata]
            )

            progress_queue.put(1)
            return bool(result)

    except Exception as e:
        logger.error(f"Error uploading {filename} to VectorDB: {e}")
        failed_files.append(filename)
        progress_queue.put(1)


def upload_vectordb(client: VectorStore, dataset_file: str) -> bool:

    # 保存上传失败的文件名的文件路径
    failed_files_path = "vector_failed_files.txt"
    # 上传失败的文件列表
    failed_files = []

    try:
        with jsonlines.open(dataset_file) as reader:

            # 使用线程池并发执行文件上传任务
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                progress_queue = Queue()
                for json_line in reader:
                    future = executor.submit(
                        upload_file_vectordb,
                        client,
                        json_line,
                        failed_files,
                        progress_queue,
                    )
                    futures.append(future)

                # Start the progress tracking thread
                progress_thread = threading.Thread(
                    target=track_progress,
                    args=(len(futures), progress_queue),
                    daemon=True,
                )
                progress_thread.start()

                # 等待所有上传任务完成。
                for future in concurrent.futures.as_completed(futures):
                    if not future.result():
                        # logger.error(f"result error:{future.result()}")
                        ...

        logger.info(f"All {len(futures)} files uploaded to VectorDB.")
        # 输出上传成功和失败数量
        success_count = len(futures) - len(failed_files)
        logger.info(f"Total files uploaded successfully: {success_count}")
        logger.info(f"Total files failed to upload: {len(failed_files)}")

        # 将上传失败的文件名保存到文件中
        if failed_files:
            with open(failed_files_path, "w") as f:
                f.write("\n".join(failed_files))

        progress_thread.join()

        return True

    except Exception as err:
        logger.exception(f"An error occurred: {err}")
        return False


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Emoji data initialization tool")
    parser.add_argument(
        "--download", action="store_true", help="Download and extract emoji data"
    )
    parser.add_argument("--upload", action="store_true", help="Upload files to MinIO")
    parser.add_argument(
        "--vectordb", action="store_true", help="Vector files to Database"
    )

    args = parser.parse_args()

    # 检查是否提供了可选参数
    if not (args.download or args.upload or args.vectordb):
        print(
            "提示: 没有提供可选参数 '--download' '--upload '--vectordb'  请至少指定一个操作。"
        )
        parser.print_help()
        exit(1)

    if args.download:

        from langchain_emoji.paths import local_data_path
        from langchain_emoji.settings.settings import settings

        # Define Google Drive file ID
        file_id = settings().dataset.google_driver_id

        # Define the directory to extract the file
        extract_dir = local_data_path

        # Download and extract the file
        success = download_and_extract_data(file_id, extract_dir)

        if not success:
            print("download and extract emoji data failed, exit!")
            exit(1)

    if args.upload:

        from langchain_emoji.settings.settings import settings
        from langchain_emoji.paths import local_data_path

        # MinIO configuration
        minio_endpoint = settings().minio.host
        minio_access_key = settings().minio.access_key
        minio_secret_key = settings().minio.secret_key
        secure = False  # Change to False if MinIO server is not using SSL/TLS

        # # Initialize MinIO client
        minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=secure,
        )

        dataset_name = settings().dataset.name
        # # Source directory containing files to upload
        source_dir = local_data_path / dataset_name / "emo"
        if not (os.path.exists(source_dir) and os.path.isdir(source_dir)):
            print("emoji datasetdoes not exist, exit!")
            exit(1)

        # # Name of the MinIO bucket
        bucket_name = "emoji"

        # # Upload files to MinIO
        success = upload_to_minio(minio_client, source_dir, bucket_name)

        if not success:
            print("upload to minio failed, exit!")
            exit(1)

    if args.vectordb:

        from langchain_emoji.paths import local_data_path
        from langchain_emoji.settings.settings import settings
        from langchain_emoji.components.vector_store import VectorStoreComponent

        vsc = VectorStoreComponent(settings())

        dataset_name = settings().dataset.name
        dataset_file = local_data_path / dataset_name / "data.jsonl"
        if not (os.path.exists(dataset_file) and os.path.isfile(dataset_file)):
            print("emoji datajsonl not exist, exit!")
            exit(1)

        # # Upload files to MinIO
        success = upload_vectordb(vsc.vector_store, dataset_file)

        if not success:
            print("upload to minio failed, exit!")
            exit(1)

    # 加载进向量数据库
