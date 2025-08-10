## Building BorgDash Docker Image (Podman + BuildKit)

To build a multiplatform image (x86_64/amd64 and arm64) with automatic versioning labels:

```bash
podman buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg VERSION=$(git describe --tags --always) \
  --build-arg REVISION=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t borgdash:latest .
```

- Requires Podman v4+ and BuildKit enabled (`podman buildx create --use` if needed)
- The image will include OCI labels for version, revision, and build date automatically
- You can push directly to a registry with `--push` if desired

## Building / Running Documentation

To build and serve the documentation locally:

```bash
pip install mkdocs-material
mkdocs serve
```

- Docs will be available at http://localhost:8000
