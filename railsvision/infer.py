import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import argparse
import os
import csv
import time

# Config
CLASSES    = ["clear_track", "vegetation"]
IMG_SIZE   = 224
DEVICE     = torch.device("cpu")  
THRESHOLD  = 0.5                 

# Image transform (same normalization as training)
infer_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# Load model
def load_model(model_path):
    model = models.resnet34(weights=None)
    model.fc = nn.Sequential(
        nn.Linear(model.fc.in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(256, len(CLASSES))
    )
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()
    print(f"Model loaded from: {model_path}")
    return model

# Run inference on a single image
def predict(model, image_path):
    img = Image.open(image_path).convert("RGB")
    tensor = infer_transform(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, pred_idx = torch.max(probs, 1)

    label      = CLASSES[pred_idx.item()]
    confidence = confidence.item()
    flagged    = label == "vegetation" and confidence >= THRESHOLD

    return label, confidence, flagged

# Main — batch inference over a folder or single image
def main(args):
    model = load_model(args.model)

    # Collect input paths
    if os.path.isdir(args.input):
        valid_ext = {".jpg", ".jpeg", ".png", ".bmp"}
        image_paths = sorted([
            os.path.join(args.input, f)
            for f in os.listdir(args.input)
            if os.path.splitext(f)[1].lower() in valid_ext
        ])
    else:
        image_paths = [args.input]

    print(f"Running inference on {len(image_paths)} image(s)...\n")

    results = []
    flagged_count = 0

    for path in image_paths:
        start = time.time()
        label, confidence, flagged = predict(model, path)
        elapsed_ms = (time.time() - start) * 1000

        status = "FLAGGED" if flagged else "OK"
        print(f"[{status}] {os.path.basename(path):40s} "
              f"| {label:15s} | conf: {confidence:.4f} | {elapsed_ms:.1f}ms")

        results.append({
            "filename":   os.path.basename(path),
            "label":      label,
            "confidence": round(confidence, 4),
            "flagged":    flagged,
            "latency_ms": round(elapsed_ms, 2)
        })

        if flagged:
            flagged_count += 1

    # Summary
    print(f"\n--- Summary ---")
    print(f"Total frames:    {len(results)}")
    print(f"Flagged (veg):   {flagged_count}")
    print(f"Clear:           {len(results) - flagged_count}")

    # Save results to CSV
    if args.output:
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to: {args.output}")

# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RailVision inference script")
    parser.add_argument("--input",  required=True,  help="Path to image file or folder of frames")
    parser.add_argument("--model",  required=True,  help="Path to trained .pth model file")
    parser.add_argument("--output", default="results.csv", help="Path to save results CSV")
    args = parser.parse_args()
    main(args)
