#!/usr/bin/env python3
"""
Manual bike counter — generate ground truth count events from a video clip.

Written by Claude (Anthropic) as a throwaway utility for the bikecounter
project. Reviewed before use, not hand-written.

Plays a clip and logs keypress events to CSV so pipeline output can be
diffed against a human count.

Keys:
    n      northbound crossing
    s      southbound crossing
    b      mark last event as bus/car rack (adds note)
    u      undo last event
    space  pause / resume
    [ ]    slower / faster playback
    ,  .   step back / forward one frame (while paused)
    q      quit and save

Raw .h264 has no container index, so seeking with CAP_PROP_POS_FRAMES is
unreliable — frame position is tracked manually and recent frames are kept
in a ring buffer to support stepping backwards.
"""

import argparse
import csv
from collections import deque
from pathlib import Path

import cv2


def format_time(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:05.2f}"


def draw_hud(frame, counts, elapsed, speed, paused, cursor, last_event):
    status = ""
    if paused:
        status = f"  [PAUSED{f' {cursor:+d}' if cursor else ''}]"

    lines = [
        f"time  {format_time(elapsed)}",
        f"NB    {counts['NB']}",
        f"SB    {counts['SB']}",
        f"speed {speed:.2f}x{status}",
    ]
    if last_event:
        lines.append(f"last  {last_event}")

    y = 30
    for line in lines:
        cv2.putText(frame, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 255, 255), 1, cv2.LINE_AA)
        y += 28
    return frame


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="CSV output path (default: <video>_manual_counts.csv)")
    ap.add_argument("--fps", type=float, default=15.0,
                    help="Source fps; raw .h264 does not report it (default 15)")
    ap.add_argument("--scale", type=float, default=0.5,
                    help="Display scale factor (default 0.5)")
    ap.add_argument("--buffer", type=int, default=30,
                    help="Frames kept in memory for stepping back (default 30)")
    args = ap.parse_args()

    out_path = args.output or args.video.with_name(
        args.video.stem + "_manual_counts.csv")

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"Could not open {args.video}")

    fps = args.fps
    events = []
    counts = {"NB": 0, "SB": 0}
    speed = 1.0
    paused = False
    last_event = ""

    # (index, frame) for the most recent frames, newest last
    buffer = deque(maxlen=max(2, args.buffer))
    cursor = 0          # 0 = newest buffered frame, negative = stepped back
    next_index = 0      # index the next read() will produce

    def read_next() -> bool:
        nonlocal next_index
        ok, frame = cap.read()
        if not ok:
            return False
        buffer.append((next_index, frame))
        next_index += 1
        return True

    if not read_next():
        raise SystemExit("Could not read any frames")

    print(f"Counting {args.video.name} at {fps} fps -> {out_path}")
    print("n=NB  s=SB  b=rack  u=undo  space=pause  [ ]=speed  , .=step  q=quit")

    while True:
        if not paused and cursor == 0:
            if not read_next():
                print("End of video.")
                break

        frame_idx, frame = buffer[len(buffer) - 1 + cursor]
        elapsed = frame_idx / fps

        display = cv2.resize(frame, None, fx=args.scale, fy=args.scale)
        display = draw_hud(display, counts, elapsed, speed,
                           paused, cursor, last_event)
        cv2.imshow("manual bike counter", display)

        delay = 30 if paused else max(1, int(1000 / (fps * speed)))
        key = cv2.waitKey(delay) & 0xFF

        if key == 255:
            continue

        if key == ord("q"):
            break

        elif key == ord(" "):
            paused = not paused

        elif key in (ord("n"), ord("s")):
            direction = "NB" if key == ord("n") else "SB"
            counts[direction] += 1
            events.append({
                "frame": frame_idx,
                "timestamp": format_time(elapsed),
                "seconds": round(elapsed, 2),
                "direction": direction,
                "note": "",
            })
            last_event = f"{direction} @ {format_time(elapsed)}"

        elif key == ord("b") and events:
            events[-1]["note"] = "rack"
            last_event = (f"{events[-1]['direction']} @ "
                          f"{events[-1]['timestamp']} (rack)")

        elif key == ord("u") and events:
            removed = events.pop()
            counts[removed["direction"]] -= 1
            last_event = f"undid {removed['direction']} @ {removed['timestamp']}"

        elif key == ord("["):
            speed = max(0.25, speed / 2)

        elif key == ord("]"):
            speed = min(8.0, speed * 2)

        elif key == ord(",") and paused:
            # step back through the ring buffer; no seeking involved
            if cursor > -(len(buffer) - 1):
                cursor -= 1

        elif key == ord(".") and paused:
            if cursor < 0:
                cursor += 1
            elif not read_next():
                print("End of video.")
                break

    cap.release()
    cv2.destroyAllWindows()

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["frame", "timestamp", "seconds", "direction", "note"])
        writer.writeheader()
        writer.writerows(events)

    print(f"\nNB: {counts['NB']}   SB: {counts['SB']}   total: {len(events)}")
    print(f"Wrote {len(events)} events to {out_path}")


if __name__ == "__main__":
    main()
