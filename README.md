# pic2video-morph-service

Generate smooth morphing videos between 2–N images via a REST API and a minimal web UI. CPU-only classical morphing is implemented; the system is designed to plug in GPU-based engines (RIFE, diffusion) later without changing the API.

## Overview

- FastAPI app exposing `/api/v1/morph` for uploads and `/` for a simple UI.
- Classical morphing: grid-based Delaunay triangulation + per-triangle affine warps + cross-dissolve.
- Outputs MP4 (H.264 via ffmpeg) with configurable frames per transition and FPS.
- Containerized and deployable to Kubernetes (GKE-compatible), also runs on RunPod unchanged.

### Architecture

```
app/
  main.py                 # FastAPI entrypoint
  api/
    routes_morph.py       # REST endpoints
    schemas.py            # Pydantic models
  services/
    morph_service.py      # Orchestrates storage + morph pipeline
    storage_service.py    # Filesystem IO and job metadata
  core/
    config.py             # Env config
    logging.py            # JSON logging setup
    exceptions.py         # HTTP exceptions
  morph/
    base.py               # Engine interface + factory
    classical_morph.py    # OpenCV-based morph implementation
    pipeline.py           # N-image sequencing + video encoding
web/
  templates/index.html    # Minimal UI
  static/styles.css       # Styling
  static/app.js           # Frontend JS
k8s/                      # Kubernetes manifests
docker/Dockerfile         # Production image
```

## How the classical morph works

1. Images are resized to match the first image.
2. Build a regular grid (default 20×20) of control points and generate Delaunay triangles.
3. For each in-between step `t` in (0,1):
   - Interpolate control points between A and B.
   - For every triangle, compute affine warp A→interp and B→interp and splat into the output canvas.
   - Cross-dissolve the two warped images with `(1-t)` and `t` weights.
4. For N images, repeat for each pair and concatenate frames; include endpoints so sequence is continuous.
5. Encode frames to MP4 using ffmpeg/libx264 with pixel format yuv420p for broad compatibility.

## Run locally (Python)

Prereqs: Python 3.11, ffmpeg installed (Docker image includes it).

```
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Open http://localhost:8080 to use the UI. API docs at http://localhost:8080/docs.

## Run with Docker

```
docker build -t pic2video-morph-service:latest .
docker run --rm -p 8080:8080 -e APP_PORT=8080 pic2video-morph-service:latest
```

Persist outputs:

```
docker run --rm -p 8080:8080 -v $(pwd)/data:/app/data pic2video-morph-service:latest
```

## Run with Docker Compose (recommended)

1) Copy and edit env:

```
cp .env.example .env
# edit HOST_PORT / limits if needed
```

2) Up:

```
docker compose up --build
```

Access the UI at http://localhost:${HOST_PORT:-8090}. The app listens on `APP_PORT` inside the container (default 8080), and Compose maps it to `HOST_PORT`.

## Kubernetes (GKE-compatible)

1. Build & push image (example uses Docker Hub; GKE Artifact Registry works as well):

```
docker build -t YOUR_REGISTRY/pic2video-morph-service:latest .
docker push YOUR_REGISTRY/pic2video-morph-service:latest
```

2. Update `k8s/deployment.yaml` image field to your registry.

3. Apply manifests:

```
kubectl apply -f k8s/
```

- Service is of type `LoadBalancer` (port 80 → 8080).
- Ingress is a generic Nginx-style spec. Configure host and TLS as needed.
- Resource requests fit CPU-only OpenCV; comment notes show how to add GPU resource requests if you add GPU engines later.

## Run on RunPod

This service is a self-contained HTTP server. To run on RunPod:

- Use the same Docker image. Set env vars as needed.
- Map container port `8080` to an external port.
- Optionally mount a persistent volume to `/app/data` to keep generated videos.
- No cloud-specific dependencies are required.

## API summary

- POST `/api/v1/morph` (multipart/form-data)
  - fields:
    - `files`: 2+ images (JPEG/PNG)
    - `frames_per_transition` (int, default 30)
    - `fps` (int, default 30)
    - `method` (enum: classical|rife|diffusion; only classical implemented)
  - returns: `video/mp4` stream

Example:

```
curl -X POST \
  -F "files=@/path/a.jpg" \
  -F "files=@/path/b.jpg" \
  -F frames_per_transition=30 \
  -F fps=30 \
  -F method=classical \
  http://localhost:8080/api/v1/morph -o morph.mp4
```

## Configuration (env vars)

- `APP_HOST` (default `0.0.0.0`)
- `APP_PORT` (default `8080`)
- `MORPH_WORK_DIR` (default `./data`)
- `MAX_UPLOAD_IMAGES` (default `10`)
- `MAX_IMAGE_SIZE_MB` (default `25`)
- `ALLOWED_IMAGE_TYPES` (default `image/jpeg,image/png`)
- `DEFAULT_FRAMES_PER_TRANSITION` (default `30`)
- `DEFAULT_FPS` (default `30`)

## Known limitations / future work

- Only classical morphing is implemented; add RIFE for high-quality frame interpolation.
- Add diffusion-based morphing leveraging Stable Diffusion or similar techniques.
- Optional background worker (e.g., Celery/Redis) for long jobs; current implementation is synchronous.
- H.264 requires ffmpeg; Docker image includes ffmpeg, but some platforms may prefer `avc1` via OpenCV if available.

## License

MIT
