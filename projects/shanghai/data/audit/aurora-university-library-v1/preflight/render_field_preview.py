"""Render the simplified field front from the measured 2020 photograph position."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from check_window_pitch import INPUT, PROJECT, homography

sys.path[:0] = [
    str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'),
    str(INPUT.parent / 'source'),
]
from library_front import PALETTE, building
from photo_architecture import Builder


def make_camera():
    measured = json.loads(INPUT.read_bytes())['floor_height_estimate']
    face, _ = homography(measured['photo25_near_level']['points'])
    pitch = measured['chosen_storey_pitch_m']
    # Recover inward depth from the two vanishing directions. Nearly level
    # sight lines leave the focal length uncertain; 620 px is an estimate.
    intrinsics = np.array([[620., 0, 420], [0, 620., 315], [0, 0, 1.]])
    right = np.linalg.solve(intrinsics, face[:, 0])
    up = np.linalg.solve(intrinsics, face[:, 1] / pitch)
    inward = np.cross(up, right)
    inward *= np.linalg.norm(right) / np.linalg.norm(inward)
    if inward[2] < 0:
        inward *= -1
    depth_axis = intrinsics @ inward

    def project(points):
        x, y, z = points.T
        camera = x[:, None] * face[:, 0] + ((z - 13.05) / pitch)[:, None] * face[:, 1]
        camera += face[:, 2] + (y - .40)[:, None] * depth_axis
        return np.column_stack([camera[:, :2] / camera[:, 2, None], 1 / camera[:, 2]])

    return project


def paint_triangle(canvas, depth, triangle, color):
    """Use barycentric coordinates to select the visible surface at each pixel."""
    a, b, c = triangle
    determinant = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if abs(determinant) < .0001:
        return
    height, width = depth.shape
    left, top = np.maximum(0, np.floor(triangle[:, :2].min(0)).astype(int))
    right, bottom = np.minimum([width-1, height-1], np.ceil(triangle[:, :2].max(0)).astype(int))
    if left > right or top > bottom:
        return
    x, y = np.meshgrid(np.arange(left, right+1)+.5, np.arange(top, bottom+1)+.5)
    u = ((b[1]-c[1])*(x-c[0]) + (c[0]-b[0])*(y-c[1])) / determinant
    v = ((c[1]-a[1])*(x-c[0]) + (a[0]-c[0])*(y-c[1])) / determinant
    z = a[2]*u + b[2]*v + c[2]*(1-u-v)
    region = np.s_[top:bottom+1, left:right+1]
    visible = (u >= 0) & (v >= 0) & (u+v <= 1) & (z > depth[region]+.000001)
    depth[region][visible] = z[visible]
    canvas[region][visible] = color


def render(output):
    builder = Builder(PALETTE)
    building(builder, True)
    project = make_camera()
    eye = np.array([-.30, -1.32, .17])
    eye /= np.linalg.norm(eye)
    light = np.array([-.34, -.62, .75])
    light /= np.linalg.norm(light)
    canvas = np.full((630, 840, 3), [116, 126, 130], dtype=np.uint8)
    depth = np.full(canvas.shape[:2], -np.inf)
    for part in builder.parts:
        color = np.asarray(builder.palette[part['material']]['color'])
        mesh = np.asarray(part['vertices'])[np.asarray(part['triangles'])]
        normals = np.cross(mesh[:, 1]-mesh[:, 0], mesh[:, 2]-mesh[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
        front_facing = normals @ eye > -.002
        for triangle, normal in zip(mesh[front_facing], normals[front_facing]):
            linear = color * (.65 + .32*max(0, normal@light))
            srgb = np.clip(1.055*linear**(1/2.4)-.055, 0, 1)
            paint_triangle(canvas, depth, project(triangle), (srgb*255).astype(np.uint8))
    Image.fromarray(canvas).crop((62, 145, 630, 461)).save(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    render(parser.parse_args().output)
