#!/bin/bash
# Script to build the latest dev version

podman buildx build \
  --platform linux/amd64 \
  --build-arg VERSION=$(git describe --tags --always) \
  --build-arg REVISION=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t borgdash:dev .