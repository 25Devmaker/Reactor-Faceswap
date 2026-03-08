import gradio as gr
import tempfile
from workflows.face_swap import run_face_swap

#Configuration 
COMFYUI_URL = "https://4a244a3825131.notebooks.jarvislabs.net"


#Face Swap Logic 
def generate_face_swap(target_image, source_face):
    if target_image is None:
        raise gr.Error("Please upload a Target Image (the person to swap INTO).")
    if source_face is None:
        raise gr.Error("Please upload a Source Face (the face to copy FROM).")

    yield [], " Uploading images to ComfyUI..."

    try:
        image_bytes_list = run_face_swap(
            base_url          = COMFYUI_URL,
            target_image_path = target_image,
            source_face_path  = source_face,
        )

        if not image_bytes_list:
            yield [], " No output received. Check that ReActor is installed in ComfyUI."
            return

        # Save output bytes to temp files for Gradio gallery
        output_paths = []
        for i, img_bytes in enumerate(image_bytes_list):
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".png", prefix=f"faceswap_{i}_"
            )
            tmp.write(img_bytes)
            tmp.close()
            output_paths.append(tmp.name)

        yield output_paths, " Done! Face swap complete."

    except TimeoutError:
        yield [], " Timed out. Your JarvisLabs instance may be busy or sleeping."
    except Exception as e:
        yield [], f" Error: {str(e)}"


#UI
with gr.Blocks(title=" ReActor Face Swap") as demo:

    gr.Markdown("""
    # ⚡ ReActor Face Swap
    ### Swap faces instantly using ComfyUI + JarvisLabs GPU
    - **Target Image** → the body/scene you want to swap INTO
    - **Source Face** → the face you want to copy FROM
    """)

    with gr.Row():
        with gr.Column(scale=1):
            target_image = gr.Image(
                label="Target Image (swap INTO this)",
                type="filepath",
            )
            source_face = gr.Image(
                label=" Source Face (copy FROM this)",
                type="filepath",
            )
            swap_btn = gr.Button(" Run Face Swap", variant="primary", size="lg")

        with gr.Column(scale=1):
            swap_output = gr.Gallery(
                label="✨ Result",
                columns=1,
                height=500,
                object_fit="contain",
            )
            swap_status = gr.Textbox(
                label="Status",
                interactive=False,
                lines=1,
            )

    swap_btn.click(
        fn=generate_face_swap,
        inputs=[target_image, source_face],
        outputs=[swap_output, swap_status],
    )

    gr.Markdown("""
    ---
    Built with [ComfyUI](https://github.com/comfyanonymous/ComfyUI) · 
    [Gradio](https://gradio.app) · 
    [JarvisLabs](https://jarvislabs.ai) · 
    ReActor
    """)

if __name__ == "__main__":
    demo.launch()