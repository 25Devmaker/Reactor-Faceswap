import copy
from comfyui_client import ComfyUIClient

# ── Workflow template ─────────────────────────────────────────────────────────
# Node 2 = target image (swap INTO this)
# Node 3 = source face  (copy FROM this face)
# Node 4 = SaveImage    (output)

REACTOR_WORKFLOW = {
    "1": {
        "inputs": {
            "enabled": True,
            "swap_model": "inswapper_128.onnx",
            "facedetection": "retinaface_resnet50",
            "face_restore_model": "GFPGANv1.4.pth",
            "face_restore_visibility": 1,
            "codeformer_weight": 0.5,
            "detect_gender_input": "no",
            "detect_gender_source": "no",
            "input_faces_index": "0",
            "source_faces_index": "0",
            "console_log_level": 1,
            "input_image": ["2", 0],
            "source_image": ["3", 0]
        },
        "class_type": "ReActorFaceSwap"
    },
    "2": {
        "inputs": {"image": "target.png"},
        "class_type": "LoadImage"
    },
    "3": {
        "inputs": {"image": "source.png"},
        "class_type": "LoadImage"
    },
    "4": {
        "inputs": {
            "filename_prefix": "faceswap",
            "images": ["1", 0]
        },
        "class_type": "SaveImage"
    }
}

OUTPUT_NODE_ID = "4"


def run_face_swap(base_url: str, target_image_path: str, source_face_path: str) -> list:
    """
    Upload both images to ComfyUI, run the ReActor workflow,
    return swapped output as list of image bytes.
    """
    client = ComfyUIClient(base_url)

    print("[FaceSwap] Uploading target image...")
    target_name = client._upload_image(target_image_path, "target.png")

    print("[FaceSwap] Uploading source face...")
    source_name = client._upload_image(source_face_path, "source.png")

    workflow = copy.deepcopy(REACTOR_WORKFLOW)
    workflow["2"]["inputs"]["image"] = target_name
    workflow["3"]["inputs"]["image"] = source_name

    print("[FaceSwap] Running workflow...")
    return client.run_workflow(workflow, OUTPUT_NODE_ID)