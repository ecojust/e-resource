"""Street doorway of the former church school, Shanghai, 219 Jiujiang Road.

Reference: Shanghai Housing Administration's 2018 restoration, exterior detail
published June 2020 (https://m.thepaper.cn/baijiahao_7604398, photo 15).
The 2013 Commons photograph predates that work. Coordinates are (X, Z) in
profiles. Local +Y faces the street. z_top is outer rectangular stonework's
height above the pavement. width is the full stone panel including the signs.
Dimensions below express image proportions, not a measured building survey.
"""
from math import asin, cos, sin
from shapely.geometry import Polygon, box

PALETTE = {
    "219 portal dressed stone": (0.49, 0.415, 0.305),
    "219 portal pale arris": (0.62, 0.54, 0.414),
    "219 portal hollow moulding": (0.365, 0.302, 0.224),
    "219 portal stone joint": (0.363, 0.306, 0.238),
    "219 portal inner stone": (0.285, 0.237, 0.176),
    "219 portal dark entry": (0.027, 0.023, 0.019),
    "219 portal door stiles": (0.046, 0.034, 0.023),
    "219 portal upper glass": (0.090, 0.055, 0.028),
    "219 portal plaque bronze": (0.43, 0.301, 0.098),
    "219 portal plaque edge": (0.57, 0.400, 0.153),
    "219 portal pavement": (0.235, 0.234, 0.222),
}


def _arch(x, top, width, half_width, spring, crown, steps):
    """Two meeting circular arcs, with vertical tangents at the springings."""
    # Construct in rectified image units, then scale X and Z independently.
    # Reference panel's photographed width is about 0.87 of its height.
    r = 0.87 * half_width
    h = (crown - spring)
    centre = (h * h - r * r) / (2 * r)
    radius = r + centre
    theta = asin(h / radius)
    right = [
        (x + width * (-centre + radius * cos(theta * i / steps)) / 0.87,
         top * (spring + radius * sin(theta * i / steps)))
        for i in range(steps + 1)
    ]
    # The two arcs share the crown. Write that vertex exactly once.
    right[-1] = (x, top * crown)
    left = [(2 * x - px, pz) for px, pz in reversed(right[:-1])]
    return Polygon([(x - width * half_width, 0), (x + width * half_width, 0),
                    *right, *left])


def opening(x, z_top, width):
    """Opening to subtract through the host wall, before installing the doorway."""
    return _arch(x, z_top, width, 0.306, 0.465, 0.760, 20)


def build(front, x, z_top, width, detailed):
    """Build one portal. The caller supplies front.box and front.profile."""
    if z_top <= 0 or width <= 0:
        raise ValueError("Positive stone-panel height and width are required")
    h, w = z_top, width
    samples = 20 if detailed else 10
    cut = opening(x, h, w)

    def stone(name, material, face_shape, y0, y1):
        if face_shape.geom_type == "Polygon":
            front.profile(name, material, face_shape, y0, y1)
        else:
            for i, part in enumerate(face_shape.geoms):
                if part.geom_type == "Polygon" and part.area > 1e-9:
                    front.profile(f"{name} {i + 1}", material, part, y0, y1)

    def block(name, material, u0, u1, d0, d1, v0, v1):
        front.box(name, material, x + u0*w, x + u1*w, d0, d1, v0*h, v1*h)

    panel = box(x - w/2, 0, x + w/2, h).difference(cut)
    stone("219 street portal ashlar panel", "219 portal dressed stone", panel, -0.010, 0.092)
    rings = [
        (0.297, 0.464, 0.748, 0.131, "outer projecting arris", "219 portal pale arris"),
        (0.282, 0.461, 0.723, 0.108, "outer dressed bevel", "219 portal dressed stone"),
        (0.273, 0.458, 0.705, 0.076, "recessed line", "219 portal hollow moulding"),
        (0.260, 0.455, 0.686, 0.089, "inner raised arris", "219 portal pale arris"),
        (0.231, 0.450, 0.649, 0.030, "sloping inner frame", "219 portal dressed stone"),
        (0.207, 0.444, 0.615, -0.105, "shadowed jamb", "219 portal inner stone"),
    ]
    if not detailed:
        rings = [rings[0], rings[2], rings[4], rings[5]]
    outside = cut
    rear = -min(0.73, 0.14*w)
    for u, spring, crown, depth, label, material in rings:
        inside = _arch(x, h, w, u, spring, crown, samples)
        stone("219 door " + label, material, outside.difference(inside), rear, depth)
        outside = inside

    # Deep, opaque door in the full opening. No wall crosses the vestibule.
    stone("219 recessed dark door", "219 portal dark entry", outside, rear-0.080, rear)
    transom = outside.intersection(box(x-w, h*0.467, x+w, h))
    stone("219 warm upper door light", "219 portal upper glass", transom, rear, rear+0.012)
    block("219 upper door transom rail", "219 portal door stiles", -.205, .205,
          rear+0.012, rear+0.031, .461, .476)
    block("219 dark door meeting stile", "219 portal door stiles", -.0035, .0035,
          rear, rear+0.021, .005, .462)
    if detailed:
        for i,u in enumerate((-.106, 0.0, .106)):
            bar = transom.intersection(box(x+(u-.003)*w,0,x+(u+.003)*w,h))
            stone(f"219 transom mullion {i+1}", "219 portal door stiles", bar,
                  rear+0.012, rear+0.027)
        for i,v in enumerate((.519, .565)):
            bar = transom.intersection(box(x-w,(v-.0025)*h,x+w,(v+.0025)*h))
            stone(f"219 transom cross rail {i+1}", "219 portal door stiles",
                  bar, rear+0.012, rear+0.026)
        # Hairline joints in the panel, clipped away from all arch mouldings.
        for row,v in enumerate((.157,.315,.477,.639,.802,.944)):
            j = panel.intersection(box(x-w,(v-.00048)*h,x+w,(v+.00048)*h))
            stone(f"219 block course {row+1}", "219 portal stone joint", j, .092,.093)
        for row,(v0,v1) in enumerate(zip((.157,.315,.477,.639,.802),(.315,.477,.639,.802,.944))):
            for i,u in enumerate((-.31,.08,.41) if row%2 else (-.47,-.10,.24)):
                j=panel.intersection(box(x+(u-.00040)*w,v0*h,x+(u+.00040)*w,v1*h))
                if not j.is_empty:
                    stone(f"219 ashlar bond {row+1}-{i+1}", "219 portal stone joint",j,.092,.093)

    # The bronze-coloured vertical boards are a post-renovation photo feature.
    # The photographed lettering is too small to supply a reliable inscription.
    for side,c in (("west",-.398),("east",.398)):
        block(f"219 {side} plaque rim", "219 portal plaque edge", c-.043,c+.043,
              .093,.121,.198,.552)
        block(f"219 {side} plaque face", "219 portal plaque bronze", c-.038,c+.038,
              .121,.125,.206,.544)
        block(f"219 {side} plinth cap", "219 portal pale arris",
              -.50 if c<0 else .309, -.309 if c<0 else .50, .09,.148,.149,.158)
    # Low threshold fits inside the reveals; the outer building has the street.
    block("219 door threshold", "219 portal pavement", -.206,.206,rear-.005,.131,0,.006)
