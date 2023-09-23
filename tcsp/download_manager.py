import logging
import os

import requests


def create_required_folders(file_path: str):
    logging.info(f"creating folder path {file_path}")
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)


def download_file(resource_root_url_path: str, resource_name: str, output_path: str) -> str:
    url = f"{resource_root_url_path}{resource_name}"
    output_file_path = f"{output_path}/{resource_name}"

    create_required_folders(output_file_path)

    logging.info(f"Downloading {url} into {output_file_path}")

    tf_file = requests.get(url)

    open(output_file_path, 'wb').write(tf_file.content)

    return output_file_path
