# Docker Setup for Upscayle API

## Prerequisites
- Docker installed on your system
- Docker Compose (optional, but recommended)

## Environment Setup

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Upscayl API credentials:
```
UPSCAYLE_API_KEY=your_actual_api_key
UPSCAYLE_API_URL=https://api.upscayl.org
```

## Running with Docker Compose (Recommended)

### Build and start the container:
```bash
docker-compose up -d
```

### View logs:
```bash
docker-compose logs -f
```

### Stop the container:
```bash
docker-compose down
```

### Rebuild after code changes:
```bash
docker-compose up -d --build
```

## Running with Docker CLI

### Build the image:
```bash
docker build -t upscayle-api:latest .
```

### Run the container:
```bash
docker run -d \
  --name upscayle-api \
  -p 8046:8046 \
  -e UPSCAYLE_API_KEY=your_api_key \
  -e UPSCAYLE_API_URL=https://api.upscayl.org \
  upscayle-api:latest
```

### Stop and remove the container:
```bash
docker stop upscayle-api
docker rm upscayle-api
```

## Accessing the API

- API Documentation: http://localhost:8046/docs
- API Base URL: http://localhost:8046

## Available Endpoints

- `GET /` - Health check
- `POST /upscale/images` - Async image upscaling (returns task_id)
- `GET /upscale/task/{task_id}` - Check task status
- `POST /upscale/images-sync` - Synchronous upscaling (waits for completion)

## Troubleshooting

### Check container status:
```bash
docker ps
```

### View container logs:
```bash
docker logs upscayle-api
```

### Access container shell:
```bash
docker exec -it upscayle-api bash
```

### Check environment variables:
```bash
docker exec upscayle-api env
```
