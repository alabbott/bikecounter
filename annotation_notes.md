# Annotation Notes

I'm annotating using the Roboflow web UI but I wanted to capture some thoughts while going through the process.

## Classes

I started with one class, bicycle, and previewed several images. This correctly labeled bicycles with relatively high confidence, 80%+ in most cases, with a few in the 70% range. However, the parked scooter that appears at the bottom of several frames was also labeled as a bicycle with high confidence. This makes sense, the handlebars are all that's visible and it looks like a bike.

I tried two classes, bicycle and scooter, and saw the same results, scooter handlebars labeled as a bicycle every time. Bicycle with wheels and scooter, same thing. I decided to use just one class, bicycle, and will go back and remove the false positives on the scooter handlebars manually.

## Confidence Thresholds

I then began experimenting with the confidence threshold for the SAM3 model, pushing lower and lower to find where false positives would appear. I also wanted to scan for bicycles that appeared with lower confidence than the 80-90% average I was seeing on most examples.

I saw that I could go as low as 20% before shadows of bicycles, car bumpers, tree branches, etc began to be labeled with confidences around 20-25%. I also saw one example of a bicycle with odd geometry that appeared at 47% confidence. This suggested that I could settle between 30% and 40% confidence threshold and still not generate too many false positives. I chose 30% to more likely catch weird geometry cases, and will review the labels manually to be sure there aren't false positives.

## Model Performance and Local Mining

One nice thing about the SAM3 model is that it generates much higher confidence scores on real bikes in the near and far bike lanes, when compared to the yolo26m model that I used for mining. It makes me consider if I should have tried other models locally for the mining pass, or perhaps uploaded more images to Roboflow initially for auto-labeling. 

I'm sort of compute limited with only a M4 Macbook Air and a GTX 1060, and uploading 14k frames only to label 13k of empty pavement would be a waste of credits, so I think the local pass with the yolo26m model was the right choice, but I might try other methods in the future.

## Labeling Cost

As I'm about to run auto-label, I see that SAM3 costs 1 credit / 1000 images, which makes me feel much better about choosing to mine locally and saving 13 credits on what could be empty pavement. I'm certain I'm missing northbound bikes in the near lane that yolo26m missed, but I can fix that with hand-picking frames rather than burning credits.
