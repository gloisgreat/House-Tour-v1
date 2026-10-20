#!/usr/bin/env bash
# Download every asset of a release into raw/ and verify its sha256 digest.
# Usage: scripts/fetch_release.sh <tag>   (repo gloisgreat/House-Tour-v1)
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${1:-Housev1}"
REPO=gloisgreat/House-Tour-v1
curl -sSf "https://api.github.com/repos/$REPO/releases/tags/$TAG" \
  | python3 -c 'import json,sys; [print(a["id"], a["digest"].split(":")[1], a["name"]) for a in json.load(sys.stdin)["assets"]]' \
  | while read -r id sha name; do
      if [ ! -s "raw/$name" ] || ! echo "$sha  raw/$name" | sha256sum -c --status; then
        curl -sSfL -H "Accept: application/octet-stream" -o "raw/$name" "https://api.github.com/repos/$REPO/releases/assets/$id"
      fi
      echo "$sha  raw/$name" | sha256sum -c --quiet && echo "ok $name"
    done
