# File: /comfyui/custom_nodes/comfyui_remote_media_io/src/comfyui_remote_media_io/nodes.py
# Final and corrected version for uploading videos to BunnyCDN.

import os
import requests
import folder_paths
import uuid # To generate unique filenames

class BunnyCDNUploadVideo:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "media_file": ("*",),
                "storage_zone_name": ("STRING", {"default": ""}),
                "access_key": ("STRING", {"default": "", "multiline": True}),
                "storage_zone_region": (["Falkenstein", "New York", "Los Angeles", "Singapore", "Sydney"],),
                "remote_path": ("STRING", {"default": "videos/"}),
                "remote_filename_prefix": ("STRING", {"default": "comfyui_"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("bunny_cdn_url",)
    FUNCTION = "upload_video"
    CATEGORY = "BunnyCDN"
    OUTPUT_NODE = True

    def get_bunny_hostname(self, region: str):
        return {
            "Falkenstein": "storage.bunnycdn.com", "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com", "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file, storage_zone_name, access_key, storage_zone_region, remote_path, remote_filename_prefix=""):
        # 1. Check credentials (via node or environment variables)
        szn = storage_zone_name or os.getenv("BUNNY_STORAGE_ZONE_NAME")
        ak = access_key or os.getenv("BUNNY_ACCESS_KEY")
        if not szn or not ak:
            print("ERROR: Storage zone name or access key are not defined.")
            return {"result": ("",)}

        # 2. Save video to temporary file
        temp_dir = folder_paths.get_temp_directory()
        # Generate a unique filename to avoid conflicts and naming issues
        filename = f"{remote_filename_prefix}.mp4"
        local_filepath = os.path.join(temp_dir, filename)

        try:
            print(f"Saving video to temporary file: {local_filepath}")
            # --- FINAL CORRECTION ---
            # Call .save_to() directly on the media_file object
            media_file.save_to(local_filepath, format="mp4", codec="h264")
        except Exception as e:
            print(f"ERROR saving video to temporary file: {e}")
            return {"result": ("",)}

        # 3. Upload temporary file
        remote_full_path = os.path.join(remote_path, filename).replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{szn}/{remote_full_path}"
        headers = {"AccessKey": ak, "Content-Type": "application/octet-stream"}

        try:
            print(f"Sending '{local_filepath}' to BunnyCDN...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
                response.raise_for_status()

            public_url = f"https://{szn}.b-cdn.net/{remote_full_path}"
            print("Martine, video ti je stigao na ZecaCDN.")
            
            return {"ui": {"bunny_cdn_url": [public_url]}, "result": (public_url,)}

        except Exception as e:
            print(f"ERROR uploading to Bunny CDN: {e}")
            return {"result": ("",)}
        finally:
            # 4. Clean up temporary file after upload
            if os.path.exists(local_filepath):
                print(f"Cleaning up temporary file: {local_filepath}")
                os.remove(local_filepath)

# Register the node for ComfyUI
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}
# Display name of the node in the interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
