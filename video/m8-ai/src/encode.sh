#!/bin/bash
set -e
LANG_="$1"
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
OUT="$2"
"$FF" -y -loglevel error -framerate 30 -i "frames_${LANG_}/%04d.png" \
  -c:v libx264 -profile:v high -level 4.0 -preset slow -crf 17 \
  -pix_fmt yuv420p -movflags +faststart -r 30 "$OUT"
ls -la "$OUT"
