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

    def download(self, uri: str) -> bytes:
        """Download blob bytes from a gs:// URI."""
        prefix = f"gs://{self._bucket.name}/"
        if not uri.startswith(prefix):
            raise ValueError(f"URI {uri} does not belong to bucket {self._bucket.name}")
        path = uri[len(prefix) :]
        blob = self._bucket.blob(path)
        return blob.download_as_bytes()
