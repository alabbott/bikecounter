# bikecounter

A Raspberry Pi in a Logan Square window counting bicycles on Milwaukee Ave.

[![Counting demo](https://img.youtube.com/vi/C8gbk7H4uX4/maxresdefault.jpg)](https://youtu.be/C8gbk7H4uX4)

## Results

Two 15 minute clips held out of training and hand-counted, then compared against the pipeline.

| clip | northbound | southbound | matched | false positives |
|---|---|---|---|---|
| 17:00 rush hour | 19/19 | 9/11 | 28/30 | 0 |
| 14:00 midday | 4/4 | 7/9 | 11/13 | 0 |

Each miss is accounted for:
 - a bike on a CTA bus rack, never detected
 - a bike on the sidewalk that veered out of frame
 - two bikes obscured by large vehicles in the traffic lanes

Zero false positives across 43 bicycles, misses accounted for with reasonable causes.

## How it works

```
Raspberry Pi 4 + Camera Module 3
        ↓  rpicam-vid, 1080p @ 15fps
   raw H.264 clips
        ↓  ffmpeg, 1 frame/sec
   14,250 frames
        ↓  YOLO26m @ conf 0.05  (mining)
   994 candidate frames
        ↓  SAM 3 auto-label @ 30%, reviewed by hand
   994 labeled images
        ↓  RF-DETR small, Objects365 weights
   fine-tuned detector
        ↓  ByteTrack → LineZone
   directional counts
```

| stage | notebook |
|---|---|
| extract frames from clips | [`01_split_frames`](notebooks/01_split_frames.ipynb) |
| mine candidates with a pretrained model | [`02_find_candidates`](notebooks/02_find_candidates.ipynb) |
| upload with clip-level splits | [`03_upload_images`](notebooks/03_upload_images.ipynb) |
| track, count, evaluate | [`04_count_bikes`](notebooks/04_count_bikes.ipynb) |

## Hardware

 - Raspberry Pi 4
 - Camera Module 3
 - Packing tape, index cards, window ledge

My initial capture failed when my original packing tape "mount" failed and I recorded 6 hours of my empty kitchen. After adding a notecard and a bit more tape, I was able to successfully capture 6 hours of traffic and empty road, with a few bikes - roughly 1,000 out of my selected training clips.

## Not done yet

 - Deployment. The frame rate floor rules out CPU inference on the Pi 4, options include an accelerator, a separete inference node, a lighter model, or cloud inference (probably not worth it for a hobby project).

## Stack

Raspberry Pi OS · Python · OpenCV · Roboflow (SAM 3, RF-DETR,
Inference) · supervision · trackers · Ultralytics · uv