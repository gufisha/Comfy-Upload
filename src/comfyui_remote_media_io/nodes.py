# File: /comfyui/custom_nodes/comfyui_remote_media_io/src/comfyui_remote_media_io/nodes.py

import os
import requests
import folder_paths
import uuid
import subprocess
import soundfile as sf

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

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

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
            return {"ui": {"bunny_cdn_url": [""]}, "result": ("",)}

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
            return {"ui": {"bunny_cdn_url": [""]}, "result": ("",)}

        # 3. Upload temporary file
        remote_full_path = os.path.join(remote_path, filename).replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{szn}/{remote_full_path}"
        headers = {"AccessKey": ak, "Content-Type": "application/octet-stream"}

        try:
            print(f"Sending '{local_filepath}' to BunnyCDN...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers, timeout=120)
                response.raise_for_status()

            public_url = f"https://{szn}.b-cdn.net/{remote_full_path}"
            print(f"BUNNY_CDN_URL url={public_url}")

            return {
                "ui": {"bunny_cdn_url": [public_url]},
                "result": (public_url,),
            }

        except Exception as e:
            print(f"ERROR uploading to Bunny CDN: {e}")
            return {"ui": {"bunny_cdn_url": [""]}, "result": ("",)}
        finally:
            # 4. Clean up temporary file after upload
            if os.path.exists(local_filepath):
                print(f"Cleaning up temporary file: {local_filepath}")
                os.remove(local_filepath)

class BunnyCDNUploadAudio:
    AUDIO_FORMATS = {
        "mp3": {"ext": ".mp3", "content_type": "audio/mpeg"},
        "wav": {"ext": ".wav", "content_type": "audio/wav"},
        "flac": {"ext": ".flac", "content_type": "audio/flac"},
        "ogg": {"ext": ".ogg", "content_type": "audio/ogg"},
    }

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "audio_format": (["mp3", "wav", "flac", "ogg"],),
                "storage_zone_name": ("STRING", {"default": ""}),
                "access_key": ("STRING", {"default": "", "multiline": True}),
                "storage_zone_region": (["Falkenstein", "New York", "Los Angeles", "Singapore", "Sydney"],),
                "remote_path": ("STRING", {"default": "audio/"}),
                "remote_filename_prefix": ("STRING", {"default": "comfyui_"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("bunny_cdn_url",)
    FUNCTION = "upload_audio"
    CATEGORY = "BunnyCDN"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def get_bunny_hostname(self, region: str):
        return {
            "Falkenstein": "storage.bunnycdn.com", "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com", "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }.get(region, "storage.bunnycdn.com")

    def upload_audio(self, audio, audio_format, storage_zone_name, access_key, storage_zone_region, remote_path, remote_filename_prefix=""):
        szn = storage_zone_name or os.getenv("BUNNY_STORAGE_ZONE_NAME")
        ak = access_key or os.getenv("BUNNY_ACCESS_KEY")
        if not szn or not ak:
            print("ERROR: Storage zone name or access key are not defined.")
            return {"ui": {"bunny_cdn_url": [""]}, "result": ("",)}

        fmt = self.AUDIO_FORMATS[audio_format]
        temp_dir = folder_paths.get_temp_directory()
        filename = f"{remote_filename_prefix}{fmt['ext']}"
        local_filepath = os.path.join(temp_dir, filename)

        try:
            print(f"Saving audio to temporary file: {local_filepath}")
            waveform = audio["waveform"].squeeze(0).cpu().numpy().T
            sample_rate = audio["sample_rate"]
            if audio_format == "mp3":
                wav_path = local_filepath + ".wav"
                sf.write(wav_path, waveform, sample_rate)
                subprocess.run(
                    ["ffmpeg", "-y", "-i", wav_path, "-b:a", "320k", local_filepath],
                    check=True, capture_output=True,
                )
                os.remove(wav_path)
            else:
                sf.write(local_filepath, waveform, sample_rate)
        except Exception as e:
            print(f"ERROR saving audio to temporary file: {e}")
            return {"ui": {"bunny_cdn_url": [""]}, "result": ("",)}

        remote_full_path = os.path.join(remote_path, filename).replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{szn}/{remote_full_path}"
        headers = {"AccessKey": ak, "Content-Type": fmt["content_type"]}

        try:
            print(f"Sending '{local_filepath}' to BunnyCDN...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers, timeout=120)
                response.raise_for_status()

            public_url = f"https://{szn}.b-cdn.net/{remote_full_path}"
            print(f"BUNNY_CDN_URL url={public_url}")

            return {
                "ui": {"bunny_cdn_url": [public_url]},
                "result": (public_url,),
            }

        except Exception as e:
            print(f"ERROR uploading to Bunny CDN: {e}")
            return {"ui": {"bunny_cdn_url": [""]}, "result": ("",)}
        finally:
            if os.path.exists(local_filepath):
                print(f"Cleaning up temporary file: {local_filepath}")
                os.remove(local_filepath)


NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo,
    "BunnyCDNUploadAudio": BunnyCDNUploadAudio,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video",
    "BunnyCDNUploadAudio": "BunnyCDN Upload Audio",
}
