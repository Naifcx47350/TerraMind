#!/bin/sh
# Reference script — same steps as docker/model-api/Dockerfile and docker/gateway/Dockerfile.
# Not COPY'd into images (Windows CRLF breaks Linux shebang). Logic is inlined in Dockerfiles.

set -e

pip install --no-cache-dir --upgrade pip

pip install --no-cache-dir \
  --index-url https://download.pytorch.org/whl/cpu \
  "torch>=2.0,<3"

pip install --no-cache-dir -r requirements.txt
