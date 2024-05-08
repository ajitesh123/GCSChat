class GCloudStorage:
    def __init__(self, bucket_name):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def upload_blob(self, file_stream, destination_blob_name):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(file_stream.read(), content_type='application/pdf')
        return blob.public_url
