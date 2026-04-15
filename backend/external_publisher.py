# -*- coding: utf-8 -*-
"""
Handles publishing protocols and results to external platforms like Figshare and protocols.io.
"""

import requests
import json
import hashlib
import os
import tempfile
from typing import Dict, Any

from backend.config import FIGSHARE_PERSONAL_TOKEN

class FigsharePublisher:
    """
    Manages the process of creating an article on Figshare, uploading files to it,
    and publishing it.
    """
    BASE_URL = "https://api.figshare.com/v2/account"

    def __init__(self, token: str):
        if not token:
            raise ValueError("Figshare personal token is required.")
        self.token = token
        self.headers = {"Authorization": f"token {self.token}"}

    def _create_article(self, title: str, description: str) -> int:
        """Creates a new, private article on Figshare."""
        article_data = {
            "title": title,
            "description": description,
            "defined_type": "dataset",  # Good default for code + results
            "keywords": ["Opentrons", "Lab Automation", "AI-Generated", "Protocol"]
        }
        response = requests.post(f"{self.BASE_URL}/articles", headers=self.headers, json=article_data)
        response.raise_for_status()  # Will raise an exception for 4xx/5xx errors
        location = response.json()["location"]
        return int(location.split('/')[-1])

    def _upload_file_part(self, upload_url: str, part: Dict[str, Any], stream):
        """Uploads a single part of a file."""
        stream.seek(part['startOffset'])
        data_chunk = stream.read(part['endOffset'] - part['startOffset'] + 1)
        requests.put(upload_url, data=data_chunk).raise_for_status()

    def _upload_file(self, article_id: int, file_path: str):
        """Manages the multi-step file upload process for a single file."""
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        with open(file_path, 'rb') as f:
            md5 = hashlib.md5()
            while True:
                chunk = f.read(1048576)
                if not chunk:
                    break
                md5.update(chunk)
            md5_hash = md5.hexdigest()

        # 1. Initiate file upload
        file_info = {"name": file_name, "md5": md5_hash, "size": file_size}
        init_url = f"{self.BASE_URL}/articles/{article_id}/files"
        response = requests.post(init_url, headers=self.headers, json=file_info)
        response.raise_for_status()
        file_location = response.json()['location']

        # 2. Get upload parts information
        response = requests.get(file_location, headers=self.headers)
        response.raise_for_status()
        upload_details = response.json()
        
        # 3. Upload all parts
        upload_url = upload_details['upload_url']
        with open(file_path, 'rb') as stream:
            for part in upload_details['parts']:
                self._upload_file_part(upload_url, part, stream)

        # 4. Complete the upload
        requests.post(file_location, headers=self.headers).raise_for_status()

    def _publish_article(self, article_id: int) -> str:
        """Publishes the article, making it public."""
        publish_url = f"{self.BASE_URL}/articles/{article_id}/publish"
        response = requests.post(publish_url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('location', '')

    def publish(self, title: str, description: str, files_to_upload: Dict[str, str]) -> str:
        """
        Main public method to orchestrate the entire publishing process.

        Args:
            title: The title for the Figshare article.
            description: The description for the article.
            files_to_upload: A dictionary where keys are desired filenames
                             and values are the string content for those files.

        Returns:
            The URL of the published article on Figshare.
        """
        article_id = self._create_article(title, description)

        with tempfile.TemporaryDirectory() as temp_dir:
            for filename, content in files_to_upload.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self._upload_file(article_id, file_path)
        
        published_url = self._publish_article(article_id)
        return published_url

# Example usage pattern (for testing):
# if __name__ == '__main__':
#     publisher = FigsharePublisher(token=FIGSHARE_PERSONAL_TOKEN)
#     test_files = {
#         "protocol.py": "print('hello world')",
#         "simulation.log": "This is a test log."
#     }
#     try:
#         url = publisher.publish(
#             title="Test Protocol from Publisher",
#             description="This is a test.",
#             files_to_upload=test_files
#         )
#         print(f"Successfully published to: {url}")
#     except Exception as e:
#         print(f"An error occurred: {e}") 