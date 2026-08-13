#!/bin/bash
# ~/bikecounter/capture_scheduled.sh
# Records 15-min clips, but only between 5:00am and 10:00am

OUTDIR="./footage"
DURATION_MS=900000   # 15 minutes
WIDTH=1920
HEIGHT=1080
FPS=15

START_HOUR=13
END_HOUR=19

mkdir -p "$OUTDIR"

# Wait until start time if we're before it
wait_for_start() {
    now_hour=$(date +%-H)
    now_min=$(date +%-M)

    if [ "$now_hour" -lt "$START_HOUR" ]; then
        target=$(date -d "today $START_HOUR:00" +%s)
        now=$(date +%s)
        sleep_sec=$((target - now))
        echo "Waiting until ${START_HOUR}:00 (sleeping ${sleep_sec}s)..."
        sleep "$sleep_sec"
    fi
}

wait_for_start

echo "Starting capture window at $(date)"

while true; do
    now_hour=$(date +%-H)
    if [ "$now_hour" -ge "$END_HOUR" ]; then
        echo "Reached end of capture window ($END_HOUR:00) at $(date). Stopping."
        break
    fi

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTFILE="$OUTDIR/clip_${TIMESTAMP}.h264"

    echo "Recording: $OUTFILE"
    rpicam-vid \
        --output "$OUTFILE" \
        --timeout "$DURATION_MS" \
        --width "$WIDTH" \
        --height "$HEIGHT" \
        --framerate "$FPS" \
        --nopreview

    sleep 1
done

echo "Capture complete. Files in $OUTDIR:"
ls -lh "$OUTDIR"
