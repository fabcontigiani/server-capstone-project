from speciesnet import SpeciesNetClassifier, SpeciesNetDetector, draw_bboxes, DEFAULT_MODEL
from PIL import Image
import os

# Create output directory
os.makedirs("output", exist_ok=True)

# Initialize the detector and classifier with the default model
detector = SpeciesNetDetector(model_name=DEFAULT_MODEL)
classifier = SpeciesNetClassifier(model_name=DEFAULT_MODEL)

# Path to your image
image_path = "photos/PORTADA-CAZADORES.jpeg"

# Load the image
img = Image.open(image_path)

# Run detection (for bounding boxes)
detector_preprocessed = detector.preprocess(img)
detection_result = detector.predict(image_path, detector_preprocessed)

print(f"\nResults for {image_path}:")
print("-" * 50)

# Print detections
if "detections" in detection_result:
    print(f"Detections found: {len(detection_result['detections'])}")
    for det in detection_result["detections"]:
        print(f"  - {det['label']}: {det['conf']:.2%}")
    
    # Draw bounding boxes and save
    annotated_img = draw_bboxes(img, detection_result["detections"])
    # Convert RGBA to RGB for JPEG saving
    annotated_img = annotated_img.convert("RGB")
    output_path = "output/annotated_" + os.path.basename(image_path)
    annotated_img.save(output_path)
    print(f"\nAnnotated image saved to: {output_path}")
else:
    print("No detections found")

# Run classification
classifier_preprocessed = classifier.preprocess(img)
classification_result = classifier.predict(image_path, classifier_preprocessed)

print("\nTop 5 classifications:")
if "classifications" in classification_result:
    classes = classification_result["classifications"]["classes"]
    scores = classification_result["classifications"]["scores"]
    for i, (class_name, score) in enumerate(zip(classes, scores), 1):
        print(f"{i}. {class_name}: {score:.2%}")
else:
    print(f"Error: {classification_result}")ks