#!/usr/bin/env bash

# Show what is running on this computer without printing API keys.
set -u

echo "Container engine:"
podman --version

echo "Lago container and published ports:"
podman ps --filter name=lago-demo --format '{{.Names}} | {{.Image}} | {{.Status}} | {{.Ports}}'

check_url() {
  service_name="$1"
  service_url="$2"
  http_status=$(curl --silent --output /dev/null --write-out '%{http_code}' "$service_url")
  printf '%s: HTTP %s — %s\n' "$service_name" "$http_status" "$service_url"
}

echo "Local web services:"
check_url "Lago dashboard" "http://127.0.0.1:8080/login"
check_url "Lago API" "http://127.0.0.1:3001/health"
check_url "FastAPI demo" "http://127.0.0.1:8000/api/status"
