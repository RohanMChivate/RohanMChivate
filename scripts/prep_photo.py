#!/usr/bin/env python3
"""
scripts/prep_photo.py
Local image pre-processing pipeline for ASCII portrait generation.

Implementation:
1. CLI arg: path to photo (default: source-photo.jpg)
2. Use rembg to strip background.
3. Composite the subject onto a pure white canvas ((255, 255, 255)).
4. Convert to grayscale and apply OpenCV CLAHE (clipLimit=3.0, tileGridSize=(8, 8)).
5. Export to source-prepped.png.
"""

import os
import sys
import argparse
import numpy as np
from PIL import Image
import cv2


def create_sample_photo(path: str):
    """Creates a sample developer silhouette portrait if source-photo.jpg is not found."""
    print(f"[!] '{path}' not found. Generating sample portrait for demonstration...")
    img = np.zeros((600, 600, 3), dtype=np.uint8) + 240
    # Head & hood
    cv2.circle(img, (300, 240), 110, (50, 50, 50), -1)
    hood_pts = np.array([[190, 240], [300, 100], [410, 240]], np.int32)
    cv2.fillPoly(img, [hood_pts], (40, 40, 40))
    # Shoulders
    cv2.ellipse(img, (300, 530), (230, 170), 0, 0, 180, (40, 40, 40), -1)
    # Glasses / Visor
    cv2.rectangle(img, (230, 220), (370, 260), (20, 20, 20), -1)
    cv2.line(img, (240, 240), (360, 240), (255, 255, 255), 3)
    # Headphones
    cv2.ellipse(img, (300, 220), (140, 120), 0, 190, 350, (30, 30, 30), 18)
    cv2.rectangle(img, (160, 210), (185, 280), (20, 20, 20), -1)
    cv2.rectangle(img, (415, 210), (440, 280), (20, 20, 20), -1)
    cv2.imwrite(path, img)


def prep_photo(photo_path: str = "source-photo.jpg", output_path: str = "source-prepped.png"):
    if not os.path.exists(photo_path):
        create_sample_photo(photo_path)

    print(f"[+] Loading input photo from: {photo_path}")
    raw_pil = Image.open(photo_path)

    # 1. Use rembg to strip background (with graceful fallback if rembg model is not downloaded)
    try:
        import rembg
        print("[+] Stripping background with rembg...")
        bg_removed = rembg.remove(raw_pil)
    except Exception as e:
        print(f"[!] rembg notice: {e}. Falling back to OpenCV GrabCut / alpha separation...")
        # Fallback to GrabCut
        img_np = np.array(raw_pil.convert("RGB"))
        mask = np.zeros(img_np.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        h, w = img_np.shape[:2]
        rect = (int(w * 0.05), int(h * 0.05), int(w * 0.90), int(h * 0.90))
        cv2.grabCut(img_np, mask, rect, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        alpha = (mask2 * 255).astype(np.uint8)
        bg_removed = Image.fromarray(np.dstack((img_np, alpha)), "RGBA")

    # 2. Composite the subject onto a pure white canvas ((255, 255, 255))
    bg_removed = bg_removed.convert("RGBA")
    white_canvas = Image.new("RGBA", bg_removed.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_canvas, bg_removed).convert("RGB")

    # 3. Convert to grayscale and apply OpenCV CLAHE (clipLimit=3.0, tileGridSize=(8, 8))
    cv_gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(cv_gray)

    # 4. Export to source-prepped.png
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cv2.imwrite(output_path, enhanced_gray)
    print(f"[SUCCESS] Exported prepped image to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Pre-process photo for ASCII portrait.")
    parser.add_argument("photo", nargs="?", default="source-photo.jpg", help="Path to input photo (default: source-photo.jpg)")
    parser.add_argument("--output", "-o", default="source-prepped.png", help="Path to output image (default: source-prepped.png)")
    args = parser.parse_args()

    prep_photo(args.photo, args.output)


if __name__ == "__main__":
    main()
