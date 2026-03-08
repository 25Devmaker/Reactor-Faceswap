import json
import uuid
import time
import base64
import requests
from pathlib import Path


class ComfyUIClient:
    """
    Lightweight client that talks directly to a running ComfyUI instance
    (e.g. on JarvisLabs) via its HTTP API.
    """

    def __init__(self, base_url: str):
        # Strip trailing slash
        self.base_url  = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _upload_image(self, image_path: str, name: str) -> str:
        """Upload an image to ComfyUI's input folder. Returns the filename."""
        url = f"{self.base_url}/upload/image"
        with open(image_path, "rb") as f:
            files   = {"image": (name, f, "image/png")}
            payload = {"overwrite": "true"}
            response = requests.post(url, files=files, data=payload, timeout=30)
        response.raise_for_status()
        return response.json()["name"]

    def _queue_prompt(self, workflow: dict) -> str:
        """Send a workflow to the queue. Returns the prompt_id."""
        url     = f"{self.base_url}/prompt"
        payload = {"prompt": workflow, "client_id": self.client_id}
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["prompt_id"]

    def _poll(self, prompt_id: str, timeout: int = 120, interval: int = 3) -> dict:
        """Poll /history until the prompt is complete. Returns history entry."""
        url      = f"{self.base_url}/history/{prompt_id}"
        deadline = time.time() + timeout

        while time.time() < deadline:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            history = response.json()

            if prompt_id in history:
                return history[prompt_id]

            time.sleep(interval)

        raise TimeoutError(f"Prompt {prompt_id} did not finish within {timeout}s")

    def _get_image_bytes(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download an output image from ComfyUI."""
        url    = f"{self.base_url}/view"
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.content

    # ── Public API ────────────────────────────────────────────────────────────

    def run_workflow(self, workflow: dict, output_node_id: str) -> list[bytes]:
        """
        Queue a workflow and return the output images as a list of bytes.

        Args:
            workflow       : the API-format workflow dict (from workflow_api.json)
            output_node_id : the node ID whose images you want (e.g. "4")
        """
        prompt_id = self._queue_prompt(workflow)
        print(f"[ComfyUI] Queued → prompt_id={prompt_id}")

        history = self._poll(prompt_id)
        outputs = history.get("outputs", {})

        images = []
        node_output = outputs.get(output_node_id, {})
        for img in node_output.get("images", []):
            data = self._get_image_bytes(
                filename    = img["filename"],
                subfolder   = img.get("subfolder", ""),
                folder_type = img.get("type", "output"),
            )
            images.append(data)
            print(f"[ComfyUI] Got image → {img['filename']}")

        return images