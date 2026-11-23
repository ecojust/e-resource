"""Cosine-weighted diffuse sky for measured courtyard views. Uses the Shanghai project rasterizer.

The depth-map algorithm is shared with the Yuqing garden survey.
"""
import numpy as np

SAMPLES = 18
DEPTH_RESOLUTION = 512

def sky_maps(parts, native, renderer):
    """Build one orthographic depth map per direction, using the entire mesh."""
    vertices = np.concatenate([part[0] for part in parts])
    extent = np.linalg.norm(np.ptp(vertices, axis=0))
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    directions = np.zeros((SAMPLES, 3), dtype='float32')
    transforms = np.zeros((SAMPLES, 3, 4), dtype='float32')
    depths = np.full((SAMPLES, DEPTH_RESOLUTION, DEPTH_RESOLUTION), -np.inf, dtype='float32')

    for i, direction in enumerate(directions):
        height = (i + .5) / SAMPLES
        azimuth = i * np.pi * (3 - np.sqrt(5))
        radius = np.sqrt(1 - height * height)
        light_axis = np.array([radius * np.cos(azimuth), radius * np.sin(azimuth), height])
        direction[:] = light_axis
        horizontal = np.cross([0., 0., 1.], light_axis)
        horizontal /= np.linalg.norm(horizontal)
        vertical = np.cross(light_axis, horizontal)
        transform = transforms[i]
        transform[:, :3] = [horizontal * (DEPTH_RESOLUTION - 4) / extent,
                            vertical * (DEPTH_RESOLUTION - 4) / extent, direction]
        transform[:2, 3] = (DEPTH_RESOLUTION - 1) / 2 - transform[:2, :3] @ center
        for positions, _, _, indices, _, _ in parts:
            projected = np.ascontiguousarray(positions @ transform[:, :3].T + transform[:, 3],
                                              dtype='float32')
            native.shadow_depth(len(indices) // 3, renderer.ptr(indices), renderer.ptr(projected),
                                DEPTH_RESOLUTION, renderer.ptr(depths[i]))
    return transforms, directions, depths


