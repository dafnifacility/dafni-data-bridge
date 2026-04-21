"""
Case 1: Downloading a public dataset does not require authentication.
"""

import os
from time import sleep

from dataset_download_tool.transport.client import Client

url = "https://raw.githubusercontent.com/psf/requests/main/README.md"
destination_dir = "./data"


def main():

    print(f"Target URL: {url}")
    print(f"Destination Directory: {destination_dir}\n")

    # ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    client = Client(url=url, token="no_auth")

    print("Starting download...")
    try:
        result = client.download(url=url, destination=destination_dir, show_progress=True, calculate_checksum=True)

        print("\nDownload finished successfully!")
        print(f"Saved to: {result.destination}")
        print(f"File size: {result.size_mb:.4f} MB")
        if result.checksum:
            print(f"MD5 Checksum: {result.checksum}")

    except Exception as e:
        print(f"\nDownload failed: {e}")

    # list data in the destination directory
    print(f"\n--- Listing data in '{destination_dir}' ---")
    try:
        files = os.listdir(destination_dir)
        if not files:
            print("Directory is empty.")
        else:
            for file_name in files:
                file_path = os.path.join(destination_dir, file_name)
                # only listing files, avoiding directories if any
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f" - {file_name} ({size} bytes)")
    except Exception as e:
        print(f"Could not list directory: {e}")

    print("\nRunning my model...")
    sleep(10)
    # call your model here
    print("\nModel execution completed!")


if __name__ == "__main__":
    main()
