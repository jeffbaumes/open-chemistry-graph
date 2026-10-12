#!/bin/sh
# Render one lesson video: videos/render.sh <node-id>
# Reads videos/<node-id>.py and writes public/videos/<node-id>.mp4 (720p, 30 fps).
set -e
cd "$(dirname "$0")/.."
id="$1"
.venv/bin/manim render -qm --fps 30 --media_dir videos/.cache -o "$id.mp4" "videos/$id.py" Lesson
mkdir -p public/videos
cp "videos/.cache/videos/$id/720p30/$id.mp4" "public/videos/$id.mp4"
ls -lh "public/videos/$id.mp4"
