# RailVision: Vegetation Detection

**Swarm Intelligence Lab**

Binary image classifier that detects vegetation overgrowth on rail tracks for an autonomous 4+1 quadplane drone. Trained on 400+ images and achieved approximately 97% validation accuracy.

---

## Overview

The RailVision drone autonomously inspects rail corridors and flags sections where vegetation encroachment may obstruct the track. This classifier runs onboard a Raspberry Pi 4B, processing saved camera frames and logging results for ground station review.

**Classes:**
- `clear_track` = track is unobstructed
- `vegetation` = overgrowth detected, flagged for review

---

## Model

- Architecture: ResNet-34 pretrained on ImageNet, fine-tuned for binary classification
- Input: 224 × 224 RGB images
- Output: class label + confidence score
- Best validation accuracy: ~97%
- Inference runtime on Raspberry Pi 4B (CPU): ~80–120ms per frame

---

## Files

| File | Description |
|------|-------------|
| `train.py` | Training script — fine-tunes ResNet-34 on labeled dataset |
| `infer.py` | Inference script — runs model on saved images or frame folders |

---

## Dataset Structure

```
data/
    train/
        clear_track/     # images of unobstructed track
        vegetation/      # images of overgrown track
    val/
        clear_track/
        vegetation/
```

---

## Usage

**Train:**
```bash
python train.py
```

**Run inference on a folder of frames:**
```bash
python infer.py --input frames/ --model rail_overgrowth_classifier.pth
```

**Run inference on a single image:**
```bash
python infer.py --input frame_001.jpg --model rail_overgrowth_classifier.pth
```

Results are saved to `results.csv` with filename, label, confidence, flagged status, and latency per frame.

---

## Dependencies

```
torch
torchvision
Pillow
```

Install with:
```bash
pip install torch torchvision Pillow
```

---

## Hardware

- Raspberry Pi 4B (inference)
- Raspberry Pi CSI camera module
- Pixhawk flight controller with ArduPilot stack
- 4+1 quadplane airframe
