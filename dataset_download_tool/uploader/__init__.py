from dataset_download_tool.uploader.s3_upload import S3Client
from dataset_download_tool.uploader.azure_upload import AzureBlobClient

def get_uploader(endpoint_url: str):

    if endpoint_url.__contains__("s3"):
        return S3Client(endpoint_url)
    elif endpoint_url.__contains__("core.windows.net"):
        return AzureBlobClient(endpoint_url)