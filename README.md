---

# Nano Banana CLI

Nano Banana CLI is a minimal command-line interface for interacting with Google’s GenAI image and video generation models. It provides a simple wrapper around **Nano Banana**, **Nano Banana Pro**, and **Veo** models for generating images and videos using text prompts and optional reference images.

This tool is intended for experimentation, prototyping, and internal workflows rather than as a full-featured generation UI.

---

## Disclaimer

This project is an unofficial wrapper around Google GenAI APIs.
It is not affiliated with or endorsed by Google.

---

## Overview

The CLI supports:

* Image generation using Nano Banana and Nano Banana Pro (Gemini image models)
* Video generation using Google Veo models
* Optional reference images for both image and video generation
* Control over aspect ratio, resolution, and video duration
* Automatic logging of generations to a local history file

---

## Requirements

* Python 3.10+
* A valid **Google Gemini API key**

---

## Environment Configuration (Required)

This tool **will not run without a valid API key**.

You must set the `GEMINI_API_KEY` environment variable before using the CLI. The key is loaded at runtime and is required for **all** image and video generation commands.

### Using a `.env` file (recommended)

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

The application will fail immediately if this variable is missing.

Do not commit your `.env` file to version control.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/nano-banana-cli.git
cd nano-banana-cli
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
.venv\Scripts\activate     # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

or, if using `uv`:

```bash
uv sync
```

---

## Usage

All commands are executed through `cli.py`.

```bash
python cli.py --help
```

---

## Image Generation

Image generation is handled through Nano Banana and Nano Banana Pro.

### Basic image generation

```bash
python cli.py image \
  --prompt "A cinematic portrait with natural skin texture" \
  --output output.png
```

By default, this uses the Nano Banana (flash image) model.

---

### Using Nano Banana Pro

Nano Banana Pro supports higher detail and resolution.

```bash
python cli.py image \
  --prompt "Ultra realistic studio portrait, visible pores, soft lighting" \
  --model gemini-3-pro-image-preview \
  --resolution 4K \
  --aspect-ratio 3:4 \
  --output portrait_pro.png
```

Resolution control (`1K`, `2K`, `4K`) applies **only** to Nano Banana Pro.

---

### Image generation with reference images

```bash
python cli.py image \
  --prompt "A fashion photoshoot of the same person" \
  --model gemini-3-pro-image-preview \
  --image-paths face_ref.png body_ref.png \
  --resolution 2K \
  --output fashion.png
```

Reference image limits:

* Nano Banana: up to 3 images
* Nano Banana Pro: up to 14 images

---

## Video Generation

Video generation is handled using Google Veo models.

### Basic video generation

```bash
python cli.py video \
  --prompt "A cinematic drone shot over a misty forest at sunrise" \
  --output forest.mp4
```

---

### Video with duration and resolution

```bash
python cli.py video \
  --prompt "Slow-motion ocean waves crashing against rocks" \
  --resolution 1080p \
  --aspect-ratio 16:9 \
  --duration_seconds 6 \
  --output waves.mp4
```

---

### Video with first and last frames

```bash
python cli.py video \
  --prompt "A person walking through a futuristic city" \
  --first-frame start.png \
  --last-frame end.png \
  --output city_walk.mp4
```

---

### Video with reference images (assets)

```bash
python cli.py video \
  --prompt "A cinematic fashion walk with realistic lighting" \
  --reference character.png outfit.png \
  --model veo-3.1-fast-generate-preview \
  --output fashion_walk.mp4
```

Reference images are treated as assets and work best with Veo 3.1 models.
If an incompatible model is selected, the CLI will automatically switch to a supported one.

---

## History Logging

All successful generations are logged to:

```txt
history.json
```

Entries include:

* Prompt
* Model used
* Output filename
* Aspect ratio and resolution (images)
* Timestamp

---

## Supported Models

### Image Models

* `gemini-2.5-flash-image` (Nano Banana)
* `gemini-3-pro-image-preview` (Nano Banana Pro)

### Video Models

* `veo-2.0-generate-001`
* `veo-3.0-generate-001`
* `veo-3.0-fast-generate-001`
* `veo-3.1-generate-preview`
* `veo-3.1-fast-generate-preview`

---

## Notes and Limitations

* The CLI does not provide advanced guidance tools such as ControlNet or IP adapters
* Prompt quality is critical, especially for Nano Banana models
* Video generation progress reporting is approximate due to API limitations
* Wider image framing results in loss of micro-detail; generate high-resolution close-ups for reference quality

---

## License

MIT License

---
