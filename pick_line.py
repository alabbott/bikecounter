#!/usr/bin/env python3
"""
Pick counting line coordinates by clicking on a video frame.

Written by Claude (Anthropic) as a utility for the bikecounter project.
Reviewed before use, not hand-written.

Click two points to define a line. Coordinates print in full-resolution
frame space (clicks are scaled back up automatically).

    python pick_line.py testclips/clip_20260812_170115.h264

Keys:
    r      reset points
    q      quit
"""

import argparse
from pathlib import Path

import cv2

points = []
scale = 0.5


def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        full = (int(x / scale), int(y / scale))
        points.append(full)
        print(f"point {len(points)}: {full}")


def main():
    global scale

    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--frame", type=int, default=0,
                    help="Frame number to display (default 0)")
    ap.add_argument("--scale", type=float, default=0.5)
    args = ap.parse_args()
    scale = args.scale

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"Could not open {args.video}")

    # raw h264 has no index, so read forward rather than seek
    frame = None
    for _ in range(args.frame + 1):
        ok, frame = cap.read()
        if not ok:
            raise SystemExit("Ran out of frames")
    cap.release()

    h, w = frame.shape[:2]
    print(f"Frame size: {w}x{h}")
    print("Click two points to define the counting line. r=reset  q=quit")

    cv2.namedWindow("pick line")
    cv2.setMouseCallback("pick line", on_click)

    while True:
        display = cv2.resize(frame, None, fx=scale, fy=scale)

        # only show the two most recent points
        for p in points[-2:]:
            sp = (int(p[0] * scale), int(p[1] * scale))
            cv2.circle(display, sp, 5, (0, 0, 255), -1)

        if len(points) >= 2:
            a = (int(points[-2][0] * scale), int(points[-2][1] * scale))
            b = (int(points[-1][0] * scale), int(points[-1][1] * scale))
            cv2.line(display, a, b, (0, 255, 255), 2)

        cv2.imshow("pick line", display)
        key = cv2.waitKey(30) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("r"):
            points.clear()
            print("reset")

    cv2.destroyAllWindows()

    if len(points) >= 2:
        a, b = points[-2], points[-1]
        print("\nPass to count_bikes.py as:")
        print(f"  --line {a[0]},{a[1]} {b[0]},{b[1]}")


if __name__ == "__main__":
    main()
