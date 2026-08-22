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

My initial capture failed when my original packing tape "mount" failed and I recorded 6 hours of my empty kitchen. After adding a notecard and a bit more tape, I was able to successfully capture 6 hours of traffic and empty road, and quite a few bikes.

## Challenges

### Mining candidates from 14,250 frames

At roughly one bike per minute (guessed average over the afternoon), 14,250 extracted frames mostly contain empty road and cars. Auto-labeling all of them on Roboflow would have burned all of my free trial credits only to end up with 13k empty frames.

Running YOLO26m locally at confidence 0.05 narrowed it to 994 candidates for free. The downside is the pretrained model misses bikes that I would need the most for fine-tuning. These were largely northbound bikes which appear at a greater angle relative to the camera, making them more difficult for the pretrained model to detect.

The question that remains is whether the improvement between mining and the pipeline is due to the fine-tuning, or using RF-DETR. I plan to try the pipeline with a YOLO model as well as pretrained RF-DETR to get conclusive results, but for now it remains an open question.

### Camera angle mattered more than size

I expected the southbound lane to be harder to detect, smaller objects, further away, more shadows. The opposite turned out to be true. Far-lane bikes appear at less of an angle relative to the camera compared to northbound bikes. The model recognizes bikes from the side even at their small size, whereas the bikes viewed more from above presented a greater challenge.

The size metrics in the trained model's metrics back this up, small objects scored higher than medium.

### Frame rate has a cliff, not a slope

| effective fps | counted (of 30) |
|---|---|
| 15 | 28 |
| 7.5 | 24 |
| 5 | 6 |
| 3 | 0 |

ByteTrack associates detections between frames by IoU overlap. Below 7.5 fps a bike moves further than its own box width between frames, so consecutive boxes don't overlap at all. Loosening the threshold helps at 7.5 fps, but can't help at 5 fps.

This determines the performance floor for deployment, and likely a Pi4 running this model on CPU will fall well under this floor.

### `LineZone` is a rectangle, not a line

Several southbound bikes were detected at high confidence, tracked with a stable ID, and clearly passed the line and yet were never counted. No errors or warnings, just visibly not being counted despite everything apparently going right.

`LineZone` checks a region of interest extending perpendicular from the rendered line. It requires every anchor of the box to be inside the region when the side flip is evaluated. Because my line was slanted, and was originally set to end at the top and bottom of the frame, bikes would exit the region of interest before all anchors could agree on one side.

The fix was to extend the line well above and below the frame. The rendered line is identical, but the region of interest is extended far enough to allow bikes to fully cross through before going out of limits - which does still happen, just far enough past the line to not matter.

### mAP didn't measure the thing that mattered

The trained model scored 97.8 mAP@50 and 74.8 mAP@50-95. Neither value predicted the accuracy of the pipeline overall.

mAP gives per-frame box quality. mAP@50-95 gives a score on localization more specifically. The real keys for accuracy, particularly with pretrained models on common classes, are consistent tracking and logical counting. Loose localization turned out to not matter much, as long as the tracker could maintain a consistent ID for each bike and the `LineZone` could accurately observe each track.

It was tempting to dive into the fine-tuning and tweaking the model training, but in the end the pipeline was the more meaningful part of the project. mAP can't account for things like flicker breaking tracking, or false positives drifting over the line. These have small impacts on the model metrics, but can result in large errors in the final product.

## Not done yet

 - Deployment. The frame rate floor rules out CPU inference on the Pi 4, options include an accelerator, a separate inference node, a lighter model, or cloud inference (probably not worth it for a hobby project).
 - Comparison against pretrained YOLO and RF-DETR. Pipeline is detector agnostic thanks to supervision, just need to run the experiment.
 - A public dashboard, I think a Logan Square bike counter site would be fun.

## Stack

Raspberry Pi OS · Python · OpenCV · Roboflow (SAM 3, RF-DETR,
Inference) · supervision · trackers · Ultralytics · uv