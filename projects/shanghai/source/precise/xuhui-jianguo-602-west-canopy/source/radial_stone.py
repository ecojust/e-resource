"""Shallow dark inlaid lines on the top tread of the west entrance at Jianguo Road 602.

Coordinates are metres, X right along the wall, Y into the building, Z up. The caller
supplies the actual semicircular stone tread and its material. The visible motif is
constructed at its measured pitch and clipped to the stone and straight sill. There
is no prescribed number of divisions around an imagined full circular pavement.
"""
import math


PITCH = math.radians(8.38)


def _clip_line(a, b, cx, y0, radius, back):
    """Clip the centreline to the tread disk and the sill half-plane."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ux, uy = a[0] - cx, a[1] - y0
    qa = dx * dx + dy * dy
    if qa < 1e-18:
        return None
    qb = ux * dx + uy * dy
    discriminant = qb * qb - qa * (ux * ux + uy * uy - radius * radius)
    if discriminant <= 0:
        return None
    root = math.sqrt(discriminant)
    lo, hi = max(0., (-qb - root) / qa), min(1., (-qb + root) / qa)
    if abs(dy) > 1e-12:
        cut = (back - a[1]) / dy
        if dy > 0:
            hi = min(hi, cut)
        else:
            lo = max(lo, cut)
    elif a[1] > back:
        return None
    if hi - lo <= 1e-7:
        return None
    return ((a[0] + dx * lo, a[1] + dy * lo), (a[0] + dx * hi, a[1] + dy * hi))


def _ribbon(b, path, width, z, material, label):
    """Editable flush strap mesh with joined edges, lying above the tread by a millimetre."""
    if len(path) < 2:
        return
    normals = []
    for (x, y), (xx, yy) in zip(path, path[1:]):
        ds = math.hypot(xx - x, yy - y)
        normals.append((-(yy - y) / ds, (xx - x) / ds))
    closed = math.dist(path[0], path[-1]) < 1e-8
    vertices, faces = [], []
    for i, (x, y) in enumerate(path):
        before = normals[i - 1] if i or closed else normals[0]
        after = normals[i] if i < len(normals) else normals[0] if closed else normals[-1]
        nx, ny = before[0] + after[0], before[1] + after[1]
        scale = .5 * width / (nx * after[0] + ny * after[1])
        vertices.extend([(x + nx * scale, y + ny * scale, z), (x - nx * scale, y - ny * scale, z)])
        if i:
            k = i * 2
            faces.append((k - 2, k - 1, k + 1, k))
    b.add(vertices, faces, material, label)


def build_radial_stone(b, radius, top=.28, *, center_x=0., threshold_y=0., lod=False,
                       material='Cut stone grooves'):
    """Add the circle, fine radial cuts, scalloped ends and alternate long stone joints.

    Pass the *upper* tread radius (half the width along the straight sill). The
    half-disc is centered at (center_x, threshold_y) and projects toward -Y.
    Material should be dark, low-gloss stone. The joint is a near-flush inset line.
    """
    if radius <= 0 or not math.isfinite(radius):
        raise ValueError('upper tread radius must be finite and positive')
    # The door-side face crops the back of the decorated annulus. The stone centre
    # is just forward of the sill. Both dimensions use the independently fitted rim.
    cusp = radius * .49
    cy = threshold_y - .318 * cusp
    inner = .220 * cusp
    fine = .0037 * radius
    joint = .0058 * radius
    z = top + min(.0018, .0013 * radius)
    phase = math.radians(-.97)

    def polar(angle, length):
        return (center_x + length * math.sin(angle), cy - length * math.cos(angle))

    def draw(path, width, label):
        fragment = []
        def flush():
            if len(fragment) >= 2:
                _ribbon(b, fragment, width, z, material, label)
            fragment.clear()
        for p, q in zip(path, path[1:]):
            part = _clip_line(p, q, center_x, threshold_y, radius - width, threshold_y - width)
            if part is None:
                flush()
                continue
            a, c = part
            if fragment and math.dist(fragment[-1], a) > 1e-8:
                flush()
            if not fragment:
                fragment.append(a)
            fragment.append(c)
        flush()

    circle_segments = 48 if lod else 112
    circle = [polar(i * math.tau / circle_segments, inner) for i in range(circle_segments + 1)]
    draw(circle, joint, 'Central stone disc outline')
    half = PITCH / 2
    # The straight threshold is closer to the disc than the scallops are. Continue
    # fine grooves only up to that boundary. Keep the rearmost groove directions
    # open instead of forcing a guessed integer petal count around the full circle.
    last = int(math.floor(math.pi / PITCH))
    angles = [phase + i * PITCH for i in range(-last, last + 1)]
    for index, a in enumerate(angles):
        draw([polar(a, inner), polar(a, cusp)], fine, f'Stone radial incision {index + 1:02}')
    # At the cropped rear the angle between the last spokes is governed by the
    # photographed sector; no caps reach the sill at those directions.
    for i in range(-last, last):
        mid = phase + (i + .5) * PITCH
        left, right = math.cos(half), math.sin(half)
        n = 5 if lod else 12
        cap = []
        for k in range(n + 1):
            s = math.pi * k / n
            across = -right * math.cos(s)
            along = left + (1.038 - left) * math.sin(s)
            cap.append((center_x + cusp * (along * math.sin(mid) + across * math.cos(mid)),
                        cy + cusp * (-along * math.cos(mid) + across * math.sin(mid))))
        draw(cap, fine, f'Rounded stone petal end {i + last + 1:02}')
        if i % 2 == 1:
            draw([polar(mid, 1.038 * cusp), polar(mid, 2 * radius)], joint,
                 f'Outer tread joint {i + last + 1:02}')
