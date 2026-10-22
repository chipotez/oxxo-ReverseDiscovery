#!/bin/sh
# Run as the rootless Podman owner, from repository root, after building dist/.
set -eu
name=koodaria-public-home-v1-review
image=localhost/koodaria-public-home:v1-dev-review
if podman container exists "$name"; then
  echo "Container already exists. Inspect it; use podman start $name to resume the retained development instance." >&2
  exit 1
fi
podman build --format docker --pull=never -f infra/Containerfile -t "$image" .
podman run -d --name "$name" --network none --read-only --cap-drop all \
  --security-opt no-new-privileges --memory 128m --pids-limit 64 \
  --restart on-failure:3 --log-opt max-size=10mb \
  --label app=koodaria --label environment=development --label phase=public-home-v1 "$image"
podman healthcheck run "$name"
