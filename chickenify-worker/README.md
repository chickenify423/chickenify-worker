# Chickenify Worker

ML worker service for the Chicken Singer application. This service processes audio files to create "chicken" versions using vocal separation and DDSP-based synthesis.

## Overview

This worker service:
1. Receives audio files via API endpoint
2. Converts audio to 44.1kHz mono WAV
3. Separates vocals from instrumental using Demucs
4. Applies "chickenification" using DDSP synthesis
5. Mixes chicken vocals with original instrumental
6. Uploads result to S3 and returns download URL

## Files

- **main.py** - FastAPI server with `/infer` endpoint
- **ddsp_infer.py** - DDSP inference and audio processing logic
- **requirements.txt** - Python dependencies
- **Dockerfile** - Container configuration for deployment

## Environment Variables

Required environment variables:

```bash
WORKER_API_KEY=<your-secret-api-key>
S3_BUCKET=<your-s3-bucket-name>
S3_REGION=<aws-region>
S3_KEY=<aws-access-key-id>
S3_SECRET=<aws-secret-access-key>
MODEL_CHECKPOINT=<path-to-trained-ddsp-model> # Optional
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --host 0.0.0.0 --port 8080
```

## Docker Deployment

```bash
# Build image
docker build -t chickenify-worker .

# Run container
docker run -p 8080:8080 \
  -e WORKER_API_KEY=your-key \
  -e S3_BUCKET=your-bucket \
  -e S3_REGION=us-east-1 \
  -e S3_KEY=your-access-key \
  -e S3_SECRET=your-secret \
  chickenify-worker
```

## API Usage

**Endpoint:** `POST /infer`

**Headers:**
- `X-API-Key: <WORKER_API_KEY>`

**Body (multipart/form-data):**
- `audio` - Audio file (MP3/WAV)
- `job_id` - Job identifier
- `user_id` - User identifier  
- `s3_prefix` - S3 key for output file

**Response:**
```json
{
  "ok": true,
  "output_s3_url": "https://bucket.s3.region.amazonaws.com/path/to/output.wav",
  "duration_sec": 30.5
}
```

## Current Implementation

The current `ddsp_infer.py` uses a placeholder squeaky synthesizer. This creates a simple sine-wave chicken effect by:
- Extracting pitch (F0) and loudness from vocals using CREPE
- Generating sine waves following the vocal melody
- Producing a "squeaky" chicken-like sound

## Future: Real DDSP Model

To replace with a trained DDSP model:
1. Train a DDSP autoencoder on chicken sounds
2. Replace `placeholder_squeaky_synth()` with actual DDSP inference
3. Set `MODEL_CHECKPOINT` to your trained model path
4. Update `DDSP_READY = True`

## Dependencies

Key libraries:
- **FastAPI** - Web framework
- **Demucs** - Vocal separation
- **CREPE** - Pitch detection
- **Librosa** - Audio processing
- **DDSP** - Differentiable Digital Signal Processing
- **Boto3** - AWS S3 integration
- **FFmpeg** - Audio conversion

## Deployment Platforms

This worker can be deployed to:
- **Modal** - Serverless GPU containers
- **Replicate** - ML model hosting
- **AWS Lambda** (with custom runtime)
- **Google Cloud Run** (with GPU)
- **Any container platform** with NVIDIA GPU support

## License

Part of the Chicken Singer project.
