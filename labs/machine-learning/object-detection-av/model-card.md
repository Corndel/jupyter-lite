# YOLOS-Tiny — Model Card

## Model description
YOLOS (You Only Look at One Sequence) is an object detection model based on the Vision Transformer (ViT) architecture. The tiny variant has approximately 6.5 million parameters. It treats object detection as a sequence-to-sequence problem, using learnable detection tokens appended to image patch tokens.

## Intended use
General-purpose object detection. Not designed or validated for safety-critical applications.

## Training data
Trained on COCO 2017 (Common Objects in Context) — 118,287 training images covering 80 object categories including person, car, bicycle, truck, traffic light, and stop sign. Images are primarily from everyday scenes, predominantly captured in the United States and Western Europe.

## Performance
- COCO val2017 AP: 28.7 (AP@IoU=0.50:0.95)
- COCO val2017 AP50: 48.4

Note: These metrics reflect average performance across all 80 categories. Performance varies significantly by category — common, well-represented objects score higher.

## Limitations
- Small objects (under ~32×32 pixels) are frequently missed
- Performs poorly in low-light, rain, fog, or glare conditions
- Biased toward scenes and object appearances common in COCO (Western, urban, daytime)
- Not trained on dashcam-perspective imagery specifically
- No temporal reasoning — each frame is processed independently

## Ethical considerations
- COCO dataset reflects the biases of its collection methodology (Flickr images, US/European bias)
- Should not be used as a sole decision-maker in safety-critical systems
- Confidence scores are not calibrated probabilities — a score of 0.8 does not mean 80% reliability
