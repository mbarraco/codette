from google.cloud import storage


class StorageAdapter:
    def __init__(self, bucket_name: str) -> None:
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)

    def upload(self, destination_path: str, data: bytes) -> str:
        """Upload blob and return its gs:// URI."""
        blob = self._bucket.blob(destination_path)
        blob.upload_from_string(data)
        return f"gs://{self._bucket.name}/{destination_path}"
