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

## Thoughts on Roboflow Labeler

I manually created a project through the web UI. The upload notebook landed my 994 images in the project with a batch ready to be annotated and labeled. I chose to use the auto-labeler and was pretty happy with the results. It did have several false positives of scooters, notably a parked scooter with just the handlebars visible at the bottom of the frame, but mostly detected bicycles and correctly boxed them. The review process was as quick and painless as reviewing ~1,000 images can be I imagine. The Labeler UI was easy to use and had nice keyboard shortcuts. The process of reviewing all of the annotations took a couple hours, spread throughout the weekend when I wasn't watching the Chicago Air and Water show.

I wish the select tool would choose the smallest box first, but it defaults to the larger one pretty often. This is easy to workaround with the layers tab and probably depends on what you're labeling but over ~1,000 images of bicycles, I find I usually want to delete the smaller box, and keep the larger one.

Once I had reviewed all of the annotations, I moved the images into a dataset and created a new version. I chose to use only auto-orient for preprocessing and no augmentations, since I wasn't certain what I would need for training.

## Training on Roboflow

After finalizing my dataset, I began to train my model. I chose to use the RF-DETR model that Roboflow recommended, stuck with the default small model, and used the Objects365 pretrained weights. I left it at the default 100 epochs to start with. I chose to start with the small model and defaults where available so that I could get a good starting place without spending too many credits. Candidly, I'm not really sure how to use all of the settings available and wanted to prioritize getting results, learning from failures, and optimizing from there rather than try to learn it all at once, or optimize before I know what my problems are.

### Preprocessing and Augmentation

When I went to train the RF-DETR model, Roboflow advised resizing images to 512x512px, so I did. At this point I was trying to make progress towards results I can evaluate rather than optimize my data. That said, I did make some choices to try and avoid some foreseeable issues. I chose to fit to size and fill with black, rather than stretch a 16:9 image to 1:1, which would cause distortion in bicycle geometries. I also opted to use no augmentations, which I didn't feel would materially help for my bicycle counting use case, and would just mask the size of my dataset.

I considered trying to use the large images anyway, but decided to stick with the recommended smaller size with the default small model, again prioritizing getting a result I can evaluate quickly, rather than trying to optimize for problems I'm not sure I have.

### Issues with training

When I uploaded my images, I specified train and valid splits, but did not reserve images for a test split. Rather than going back and manually selecting the split, I let Roboflow do so automatically. This introduces the risk of adjacent frames appearing in train and test splits, which I was trying to avoid, but after spending keyboard time on reviewing and correcting annotations, I just wanted to move forward and try training a model. When I start to understand how the model performs in real world test cases, I can go back and optimize my dataset and address other failure modes. 

### Progress over perfection

I've made some choices, some better informed than others, but there are trade-offs between spending time and brainpower trying to make perfect decisions now, versus failing and iterating quickly. I need to understand how the model performs, how an off-the-shelf model like YOLO26 or RF-DETR performs, and what their failure modes on my use case actually are. If I observe false positives on non-bicycle objects, false negatives in some frames causing flicker, or poor performance on northbound or southbound bicycles then I will better understand what levers to pull when I train another model.

### Training Results

The training plateaued pretty quickly, mAP@50 starts high (95%) and never really improves. mAP@50-95 climbs from 66% to 72% by epoch 10 but doesn't improve from there. Roboflow cut the training short at 31 epochs, which was nice because it's clear there wasn't more improvement to be had and it saved me some credits.

The high initial mAP@50 performance and early plateau makes sense for a pretrained model on a common class like bicycles. I primarily want to fine tune for my specific camera angle and some of the unique bicycles in Chicago, cargo bikes, Divvy bikes, e-bikes with weird geometries.

It could also be due to a validation set that is too similar to the training set. I know this could be an issue due to the automatic assignment of train, valid, and test splits, which contain very similar frames of the same cyclist.

The takeaway from this initial training is that more epochs won't help. The model generally seems to have started good and stayed good. The weak mAP@50-95 suggests my primary issue is localization, which could be partly due to hand-drawn boxes on my training images combined with inconsistent decisions when riders partially obscured bike features. It could also be caused by the low resolution of the images and relatively small objects I'm looking for. The real tell will be how well it counts bicycles. False positives and flicker could still be real issues affecting the outcome of the project.

Next steps I'd like to try, training wise, are seeing how a YOLO model performs after fine tuning, compared to the RF-DETR model. RF-DETR seems to have started off better than the YOLO model I used for mining, it would be interesting to see how a YOLO model performs over a few epochs of training. I would also like to try feeding larger images into the RF-DETR model, and see if that improves my mAP@50-95 scores. But again, the real tell is how well I can count bikes, which I have not done yet, so that's where I'll go next.

### A note on small objects

All of my bicycles fall into the small or medium buckets, with no bicycle appearing large enough in frame to be considered large. This combined with the resizing of images to 512x512px, fit with black borders, means my small objects are, well, really small. It's still not clear to me if this will be a problem but if I have issues with the further away southbound bike lane, I may need to train and run inference on larger images. This could turn into a balancing act of compute resources on the Pi vs model performance on image size, but we'll cross that bridge when we get there.

Another interesting finding, mAP@50 on medium objects came back lower than mAP@50 on small objects (98.0% vs 99.3%). While this isn't a very meaningful result on its own, it suggests that my observations during the mining pass were correct, and the greater viewing angle on the much closer northbound bikes hinders performance more than the smaller bikes being further away, but more straight on relative to the camera.

## Testing the model

I started by counting the number of northbound and southbound bikes in two of my test clips, one with low traffic volume in the 14:00 hour (clip_20260812_140056) and one during the evening rush in the 17:00 hour (clip_20260812_170115). I had Claude write a helper to play the clip and log NB or SB bikes on a keypress and write the results to CSV. This felt like a good use of AI assistance to accelerate the process. The helper can be found in count_manual.py and could be handy again later.

I had to decide whether to count bikes being walked or bikes on the CTA bus racks would be counted as well, I decided to include all bikes in frame in the totals and will keep that in mind when placing the counting lines. The lines will need to be placed across the whole frame, including sidewalks and traffic lanes, rather than just the bike lanes. This lets me count riders in the traffic lanes or sidewalks, and doesn't add the complication of discerning a walked bike or bike on a rack.

The midday clip had 4 NB and 9 SB bikes while the rush hour clip had 19 NB and 11 SB, over double the volume and importantly, dominated by NB bikes, which the yolo26m model used for mining struggled with. The total number of bikes is ultimately quite small and will lead to higher error rates from missing or double counting 1-2 bikes, which is worth considering when evaluating model performance later.

Once I had a ground truth number, I had real data to test my pipeline against when testing different models.
