import os
import json
import click
import io
import time

from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageFile
from io import BytesIO
from typing import List, Tuple, Union # Added for type hinting

# Import the new Google Gen AI SDK (v2)
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

NANO_BANANA = "gemini-2.5-flash-image"
NANO_BANANA_PRO = "gemini-3-pro-image-preview"
VEO_MODEL = "veo-2.0-generate-001"
VEO_3_1 = "veo-3.1-generate-preview" # Needed for "asset" references
VEO_3 = "veo-3.0-generate-001"
VEO_3_1_FAST = "veo-3.1-fast-generate-preview"
VEO_3_FAST = "veo-3.0-fast-generate-001"

IMG_MODELS = [NANO_BANANA, NANO_BANANA_PRO]
VID_MODELS = [VEO_3_1, VEO_MODEL, VEO_3_1_FAST, VEO_3, VEO_3_FAST]
MODELS = IMG_MODELS + VID_MODELS
DURATION_SECONDS = [4, 6, 8]

IMAGE_LIMITS: dict[str, int] = {
    NANO_BANANA_PRO: 14,
    NANO_BANANA: 3,
    "default": 1
}

IMAGE_ASPECT_RATIOS = [
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9"
]

IMAGE_RESOLUTIONS = ["1K", "2K", "4K"]

VIDEO_ASPECT_RATIOS = ["16:9", "9:16"]
VIDEO_RESOLUTIONS = ["720p", "1080p"]

HISTORY_PATH = "history.json"

def get_client() -> genai.Client:
    """Initializes the GenAI client with the API key."""
    api_key: Union[str, None] = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise click.ClickException(
            "GEMINI_API_KEY not found. Please set it in your .env file."
        )
    return genai.Client(api_key=api_key)



def load_image_for_image(file_path: str) -> ImageFile.ImageFile:
    """Loads an image file and converts it into ImageFile"""
    if not os.path.exists(file_path):
        raise click.FileError(file_path, hint="File not found.")
    
    allowed_ext = {".jpg", ".jpeg", ".png"}
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in allowed_ext:
        raise click.FileError(
            file_path, 
            hint=f"Unsupported file type '{ext}'. Only JPEG and PNG are allowed."
        )

    return Image.open(file_path)


def load_image_for_video(file_path: str) -> types.Image:
    """Reads the image file into bytes, restricted to PNG and JPEG."""
    if not os.path.exists(file_path):
        raise click.FileError(file_path, hint="File not found.")
    
    ext = os.path.splitext(file_path)[1].lower().replace(".", "")
    
    allowed_extensions = ["jpg", "jpeg", "png"]
    if ext not in allowed_extensions:
        raise click.UsageError(
            f"Unsupported file type '{ext}'. Only JPG, JPEG, and PNG are allowed."
        )

    # Map jpg to jpeg for the standard MIME type format
    mime_ext = "jpeg" if ext in ["jpg", "jpeg"] else "png"
    mime_type = f"image/{mime_ext}"

    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    return types.Image(
        image_bytes=raw_bytes,
        mime_type=mime_type
    )



def save_to_history(entry):
    """Helper to save to the history file."""
    if not os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "w") as f:
            json.dump([], f, indent=4)

    with open(HISTORY_PATH, "r+") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=4)


@click.group()
def cli():
    """
    Nano CLI: A tool for interacting with Google's 'Nano Banana' (Gemini) models.
    """
    pass

@cli.command()
@click.option(
    "--prompt", "-p", 
    required=True, 
    help="The text description of the image you want to generate."
)
@click.option(
    "--output", "-o", 
    default="output.png", 
    help="Path to save the generated image."
)
@click.option(
    "--image-paths", "-i",
    multiple=True,
    help="One or more paths to image files to use as reference for generation. (Max 14 for Pro, 3 for Flash Image)"
)
@click.option(
    "--model", "-m", 
    default=NANO_BANANA,
    type=click.Choice(MODELS),
    help="Model ID. Defaults to Gemini 3 Pro (Nano Banana Pro)."
)
@click.option(
    "--aspect-ratio", 
    default="1:1", 
    type=click.Choice(IMAGE_ASPECT_RATIOS),
    help="The aspect ratio of the generated image."
)
@click.option(
    "--resolution", "-r",
    default="1K",
    type=click.Choice(IMAGE_RESOLUTIONS),
    help="The output resolution of the generated image. (resolution is only used for nano banana pro)"
)
def image(
    prompt: str, 
    output: str, 
    model: str, 
    image_paths: Tuple[str, ...], 
    aspect_ratio: str, 
    resolution: str,
) -> None:
    """
    Generate an image using Gemini 3 Pro Image (Nano Banana Pro).
    """
    client: genai.Client = get_client()

    click.secho(f"🍌 Calling {model}...", fg="yellow")
    click.echo(f"   Prompt: {prompt}")

    # Validation
    max_images: int = IMAGE_LIMITS.get(model, IMAGE_LIMITS.get("default"))
    if len(image_paths) > max_images:
        click.secho(
            f"❌ Error: Model '{model}' supports a maximum of {max_images} input images. You provided {len(image_paths)}.", 
            fg="red"
        )
        return
    
    # Preperation
    contents: List[Union[str, types.Part]] = []
    if image_paths:
        click.echo(f"   Reference Images: {len(image_paths)}")
        for path in image_paths:
            contents.append(load_image_for_image(path))
    
    contents.append(prompt)


    try:
        if model == NANO_BANANA:
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio
            )
        else:
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution
            )

        generate_config: types.GenerateContentConfig = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=image_config    
        )

        # Generation
        response: types.GenerateContentResponse = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_config
        )

        for part in response.parts:
            if part.inline_data:
                image = part.as_image()
                now = datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S_")
                modified_output = timestamp + output
                image.save(modified_output)
                click.secho(f"✨ Success! Image saved to: {modified_output}", fg="green")



                try:
                    image.show()
                    history_entry = {
                        "name": modified_output,
                        "prompt": prompt,
                        "reference_images": [os.path.basename(p) for p in image_paths],
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio,
                        "model": model
                    }
                    
                    save_to_history(history_entry)

                except:
                    pass
                return

        click.secho("⚠️ No image found in the response.", fg="red")

    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg="red")


@cli.command()
@click.option("--prompt", "-p", required=True, help="Text description of the video.")
@click.option("--negative-prompt", "-n", help="What to exclude from the video.")
@click.option("--output", "-o", default="output.mp4", help="Output filename.")
@click.option("--model", "-m", default=VEO_3_1_FAST, type=click.Choice(VID_MODELS))
@click.option("--aspect-ratio", default="16:9", type=click.Choice(VIDEO_ASPECT_RATIOS))
@click.option("--resolution", "-r", default="720p", type=click.Choice(VIDEO_RESOLUTIONS))
@click.option("--duration_seconds", "-d", default=4, type=click.Choice(DURATION_SECONDS))
@click.option("--first-frame", "-f", type=click.Path(exists=True), help="Image to use as the starting frame.")
@click.option("--last-frame", "-l", type=click.Path(exists=True), help="Image to use as the ending frame.")
@click.option("--reference", "-ref", multiple=True, type=click.Path(exists=True), help="Reference images (assets) for style/character.")
def video(prompt, negative_prompt, output, model, aspect_ratio, resolution, duration_seconds, first_frame, last_frame, reference):
    """
    Generate a video using Google Veo.
    """
    client = get_client()
    click.secho(f"🎬 Initializing {model} Video Task...", fg="cyan")

    # 1. Prepare Inputs
    start_img = load_image_for_video(first_frame) if first_frame else None
    end_img = load_image_for_video(last_frame) if last_frame else None
    
    ref_images = []
    if reference:
        if model not in [VEO_3_1_FAST, VEO_3_1]:
            click.secho("⚠️ Reference images ('assets') work best with veo-3.1-fast-generate-preview. Switching model...", fg="yellow")
            model = VEO_3_1_FAST
        for path in reference:
            ref_images.append(types.VideoGenerationReferenceImage(
                image=load_image_for_video(path),
                reference_type="asset"
            ))

    # 2. Start Operation
    try:
        operation = client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=start_img, # This acts as the 'first_frame' or general image prompt
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                negative_prompt=negative_prompt,
                last_frame=end_img,
                duration_seconds=duration_seconds,
                reference_images=ref_images if ref_images else None
            ),
        )

        click.echo(f"⏳ Video generation started (ID: {operation.name})...")
        
        # 3. Polling for results
        with click.progressbar(length=100, label="Generating Video") as bar:
            # We don't have a percentage, so we'll just pulse or update status
            while not operation.done:
                time.sleep(10)
                operation = client.operations.get(operation)
                # You can't really track progress percentage with this API yet, 
                # so we just show activity.
                bar.update(5) 
        
        # 4. Handle Result
        if operation.result and operation.result.generated_videos:
            for n, gen_video in enumerate(operation.result.generated_videos):
                now = datetime.now().strftime("%Y%m%d_%H%M%S_")
                final_output = f"{now}{n}_{output}"
                
                # Download and Save
                client.files.download(file=gen_video.video)
                gen_video.video.save(final_output)
                
                click.secho(f"✨ Success! Video saved to: {final_output}", fg="green")

                # Log to history
                history_entry = {
                    "type": "video",
                    "name": final_output,
                    "prompt": prompt,
                    "model": model,
                    "timestamp": str(datetime.now())
                }
                save_to_history(history_entry)
        else:
            click.secho("❌ Video generation completed but no video was returned.", fg="red")

    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg="red")




if __name__ == "__main__":
    cli()