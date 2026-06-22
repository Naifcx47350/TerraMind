# DEPRECATED — use Docker Compose for the full TerraMind stack.
#
#   cp .env.example .env
#   docker compose --profile init run --rm init-indexes   # first time
#   docker compose up --build
#
# See docker/README.md for a step-by-step explanation.
#
# This file is kept so `docker build .` does not silently use a broken recipe.
FROM alpine:3.19
RUN echo "Use: docker compose up --build  (see docker/README.md)" >&2 && exit 1
