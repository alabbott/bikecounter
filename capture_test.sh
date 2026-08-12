#!/bin/bash

OUTDIR="./footage"
DURATION_MS=60000    # 1 minute
WIDTH=1920
HEIGHT=1080
FPS=15

mkdir -p "$OUTDIR"

for i in 1 2 3; do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTFILE="$OUTDIR/test_clip_${TIMESTAMP}.h264"

    echo "Recording test clip $i: $OUTFILE"
    rpicam-vid \
        --output "$OUTFILE" \
        --timeout "$DURATION_MS" \
        --width "$WIDTH" \
        --height "$HEIGHT" \
        --framerate "$FPS" \
        --nopreview

    sleep 1
done

echo "Test run complete. Check $OUTDIR"
ls -lh "$OUTDIR"
