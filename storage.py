import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import tempfile
from typing import Optional

class AudioStorage:
    def __init__(self):
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
        
        # Check if we're using Railway's built-in storage
        self.use_railway_storage = not all([self.aws_access_key, self.aws_secret_key, self.bucket_name])
        
        if not self.use_railway_storage:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key
                )
            except Exception as e:
                print(f"Warning: Could not initialize S3 client: {e}")
                self.use_railway_storage = True

    def save_audio(self, audio_content: bytes, filename: str) -> Optional[str]:
        """
        Save audio content to storage (S3 or Railway's built-in storage)
        """
        if self.use_railway_storage:
            return self._save_to_railway_storage(audio_content, filename)
        else:
            return self._save_to_s3(audio_content, filename)

    def _save_to_s3(self, audio_content: bytes, filename: str) -> Optional[str]:
        """
        Save audio to AWS S3
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=audio_content,
                ContentType='audio/mpeg'
            )
            
            # Generate the URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
            return url
            
        except (NoCredentialsError, ClientError) as e:
            print(f"Error saving to S3: {e}")
            # Fallback to Railway storage
            return self._save_to_railway_storage(audio_content, filename)
        except Exception as e:
            print(f"Unexpected error saving to S3: {e}")
            return self._save_to_railway_storage(audio_content, filename)

    def _save_to_railway_storage(self, audio_content: bytes, filename: str) -> Optional[str]:
        """
        Save audio to Railway's built-in storage (local filesystem)
        """
        try:
            # Create audio directory if it doesn't exist
            audio_dir = 'static/audio'
            os.makedirs(audio_dir, exist_ok=True)
            
            # Save file locally
            file_path = os.path.join(audio_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(audio_content)
            
            # Return a relative URL that will work with Railway
            return f"/static/audio/{filename}"
            
        except Exception as e:
            print(f"Error saving to Railway storage: {e}")
            return None

    def delete_audio(self, filename: str) -> bool:
        """
        Delete audio file from storage
        """
        if self.use_railway_storage:
            return self._delete_from_railway_storage(filename)
        else:
            return self._delete_from_s3(filename)

    def _delete_from_s3(self, filename: str) -> bool:
        """
        Delete audio from AWS S3
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return True
        except Exception as e:
            print(f"Error deleting from S3: {e}")
            return False

    def _delete_from_railway_storage(self, filename: str) -> bool:
        """
        Delete audio from Railway's built-in storage
        """
        try:
            file_path = os.path.join('static/audio', filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting from Railway storage: {e}")
            return False 