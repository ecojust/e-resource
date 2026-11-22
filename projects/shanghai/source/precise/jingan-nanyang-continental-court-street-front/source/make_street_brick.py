"""Generate a repeatable red-brick finish from period and course measurements."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

WIDTH, HEIGHT = 768, 480
COLUMNS, COURSES = 6, 12
rng = np.random.default_rng(192705)
y, x = np.indices((HEIGHT, WIDTH))
row = y * COURSES // HEIGHT
brick_w, brick_h = WIDTH / COLUMNS, HEIGHT / COURSES
phase = (x + (row % 2) * brick_w / 2) / brick_w
column = np.floor(phase).astype(int) % COLUMNS
u, v = (phase % 1) * brick_w, y % brick_h
speckle = rng.normal(0, 1, x.shape)
fine = gaussian_filter(speckle, .65, mode='wrap') * 6.5 + 3.2 * speckle
grain = gaussian_filter(rng.normal(0, 1, x.shape), 4, mode='wrap') * 58
dx = np.minimum(u, brick_w-u) * (.238 / brick_w)
dy = np.minimum(v, brick_h-v) * (.064 / brick_h)
dist = np.minimum(dx, dy) + fine * .00012
face = np.clip((dist-.0022)/.0023, 0, 1)
tone = rng.normal(0, 8, (COURSES, COLUMNS))[row, column]
vary = rng.normal(0, 2, (COURSES,COLUMNS,3))[row, column]
brick = np.array([156,103,82]) + tone[...,None] * [1,.80,.69] + vary
mortar = np.array([167,148,130]) - np.clip((.0038-dist)/.004,0,1)[...,None] * 6
pixels = mortar*(1-face[...,None]) + brick*face[...,None]
pixels += ((fine+grain) * (.8+.2*face))[...,None]
Image.fromarray(np.uint8(np.clip(pixels,0,255))).save(Path(__file__).with_name('continental-facing-brick.jpg'),quality=93,subsampling=0,optimize=True)
