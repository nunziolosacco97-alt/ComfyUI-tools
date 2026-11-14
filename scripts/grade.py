"""Final cinematic grade: vivid saturation, warm highlights, cool shadows, gentle S-curve + warm sunset sky gradient (sky pixels only)."""
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def grade(im, sat=1.30, con=1.10):
    im = ImageEnhance.Color(im).enhance(sat)
    a = np.asarray(im).astype(np.float32) / 255.0
    lum = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])[..., None]
    hi = np.clip((lum - 0.45) / 0.55, 0, 1); lo = np.clip((0.45 - lum) / 0.45, 0, 1)
    veg = np.clip((a[..., 1] - np.maximum(a[..., 0] * 0.9, a[..., 2] * 1.05)) * 8 + 0.3, 0, 1)[..., None]   # grass / trees: no cool shadow tint, slightly warmer
    a = a * (1 + hi * np.array([0.10, 0.02, -0.12]) * float(__import__("os").environ.get("FF_WARM", "1")) + lo * np.array([-0.06, 0.0, 0.10]) * (1 - veg) + veg * np.array([0.05, 0.0, -0.08]))
    a = np.clip(a, 0, 1); a = 0.5 + (a - 0.5) * con
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def sky(im, strength=0.75):
    """tint only the bright, low-saturation pixels of the upper half (the sky) with an orange->magenta sunset gradient"""
    a = np.asarray(im).astype(np.float32) / 255.0
    H, W = a.shape[:2]
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-4)
    y = np.linspace(0, 1, H)[:, None]
    m = ((mx > 0.55) & (sat < 0.30)).astype(np.float32) * np.clip((0.55 - y) / 0.15, 0, 1)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255.0
    t = np.clip(y / 0.45, 0, 1)
    top = np.array([0.62, 0.30, 0.55]); hor = np.array([1.00, 0.62, 0.28])
    g = (top[None, None] * (1 - t[..., None]) + hor[None, None] * t[..., None])
    lum = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])[..., None]
    tinted = np.clip(g * (0.55 + 0.75 * lum), 0, 1)
    k = (m * strength)[..., None]
    return Image.fromarray((np.clip(a * (1 - k) + tinted * k, 0, 1) * 255 + 0.5).astype(np.uint8))
