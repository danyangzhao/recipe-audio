import boto3
import os
from botocore.exceptions import ClientError

class AudioStorage:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.bucket = os.getenv('S3_BUCKET_NAME')

    def save_audio(self, audio_data, filename):
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=f"audio/{filename}",
                Body=audio_data,
                ContentType='audio/mpeg'
            )
            return f"https://{self.bucket}.s3.amazonaws.com/audio/{filename}"
        except ClientError as e:
            print(f"Error saving to S3: {e}")
            return None

    def get_audio_url(self, filename):
        return f"https://{self.bucket}.s3.amazonaws.com/audio/{filename}" 