"""1914 service block. Steel lights and individual sandstone window surrounds, 2019–20 condition."""

from math import sqrt
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def _finish(rgb, roughness, metallic=0.0):
    c = [v / 255 for v in rgb]
    return dict(color=[v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c],
                roughness=roughness, metallic=metallic)


STONE = 'Window | warm fine-grained dressed stone'
EDGE = 'Window | illuminated moulded arris'
SHADE = 'Window | sheltered buff stone'
BACK = 'Window | weathered brown reveal'
IRON = 'Window | charcoal painted steel'
CASE = 'Window | dark bronze-grey case'
GLASS = 'Window | cool grey reflected sky'
DIM = 'Window | shaded reflected glass'
PALETTE = {
    STONE: _finish((170, 151, 129), .89), EDGE: _finish((193, 174, 148), .85),
    SHADE: _finish((150, 129, 107), .92), BACK: _finish((131, 112, 95), .93),
    IRON: _finish((51, 50, 47), .57, .24), CASE: _finish((78, 73, 64), .64, .16),
    GLASS: _finish((115, 132, 143), .30, .17), DIM: _finish((86, 98, 109), .35, .12),
}


def _depth_mapper(face, opening, layout):
    if face in ('north', 'front', 'street'):
        return -1., lambda t, d, z: (t, d, z)
    if face in ('east', 'short', 'end'):
        x = float(opening.get('wall_x', 0.))
        return 1., lambda t, d, z: (x + d, t, z)
    if face in ('south', 'court', 'courtyard', 'rear'):
        y = float(opening.get('wall_y', layout.get('depth', 11.33)))
        return 1., lambda t, d, z: (t, y - d, z)
    raise ValueError(f'Unregistered window face {face!r}')


def _pediment_outline(style, radius, rise, base, steps):
    if style == 'triangle':
        return [(-radius, base), (0, base + rise), (radius, base)]
    # Segmental rather than semicircular. The measured radius and sagitta fix the circular arc.
    circle_radius = (radius * radius + rise * rise) / (2 * rise)
    center_z = base + rise - circle_radius
    return [(radius * (2 * i / steps - 1),
             center_z + sqrt(max(0., circle_radius ** 2 - (radius * (2 * i / steps - 1)) ** 2)))
            for i in range(steps + 1)]


def add_window(b, face, opening, layout, lod=False):
    """Build the measured opening. Along-wall, depth, and height are expressed in metres.

    The polygon outlines are based on the frontal Qiao detail. Cornice orders are measured
    separately from the glass; the rectangular inner window continues beneath the head.
    """
    c, w, lo, hi = (float(opening[key]) for key in ('center', 'width', 'sill', 'head'))
    if not w > 0 or not hi > lo:
        raise ValueError('Window width and clear height must be positive')
    cols, rows = int(opening['cols']), int(opening['rows'])
    if min(cols, rows) < 1:
        raise ValueError('Glass counts must be positive')
    short = face in ('east', 'short', 'end')
    back = face in ('court', 'south', 'courtyard', 'rear')
    style = opening['style']
    along_sign, point = _depth_mapper(face, opening, layout)
    name = 'Hospital ' + str(opening.get('id', f"{face}{opening['axis']}-{opening['level']}")) + ' | '
    x0, x1 = c - w / 2, c + w / 2

    def solid(poly, front, rear, material, label):
        depths = sorted((along_sign * front, along_sign * rear))
        b.prism(poly, *depths, lambda t, z, v: point(t, along_sign * v, z), material, name + label)

    def strip(parts, d0, d1, material, label):
        solid(unary_union(parts), d0, d1, material, label)

    def detail(coords):
        return Polygon([(c + u * w, hi + v * w) for u, v in coords])

    inset = float(opening.get('inset', .21 if short else (.25 if back else .42)))
    rim = min(.055, .034 * w)
    edge_w = .013 * w
    # Each return ends at the exterior jamb and the frame face. An empty centre stays clear.
    mouth = box(x0, lo, x1, hi)
    reveal = mouth.difference(box(x0 + edge_w, lo + edge_w, x1 - edge_w, hi - edge_w))
    solid(reveal, -.002, inset + .060, BACK, 'four deep returns')
    inner = box(x0 + rim, lo + rim, x1 - rim, hi - rim)
    frame = box(x0 + edge_w, lo + edge_w, x1 - edge_w, hi - edge_w).difference(inner)
    solid(frame, inset, inset + .066, CASE, 'painted fixed perimeter')

    x0g, z0g, x1g, z1g = inner.bounds
    glass_w, glass_h = x1g - x0g, z1g - z0g
    xl = [x0g + glass_w * i / cols for i in range(cols + 1)]
    zl = [z0g + glass_h * j / rows for j in range(rows + 1)]
    glazing = []
    dark_glazing = []
    verticals = []
    horizontals = []
    if lod:
        solid(inner, inset + .052, inset + .065, GLASS, 'glazing behind steel grid')
    else:
        for i in range(cols):
            for j in range(rows):
                pane = box(xl[i] + .0015, zl[j] + .0015, xl[i + 1] - .0015, zl[j + 1] - .0015)
                (dark_glazing if (i + 2*j + int(opening['axis'])) % 7 == 1 else glazing).append(pane)
        if glazing:
            strip(glazing, inset + .052, inset + .065, GLASS, 'daylit glass lights')
        if dark_glazing:
            strip(dark_glazing, inset + .052, inset + .065, DIM, 'shaded glass lights')
    for i in range(1, cols):
        thick = max(.012, min(.035, (.021 if i * 2 == cols else .013) * w))
        verticals.append(box(xl[i] - thick / 2, z0g, xl[i] + thick / 2, z1g))
    for j in range(1, rows):
        thick = max(.012, min(.030, (.017 if j == rows-2 else .012) * w))
        horizontals.append(box(x0g, zl[j] - thick / 2, x1g, zl[j] + thick / 2))
    if verticals or horizontals:
        strip(verticals + horizontals, inset + .019, inset + .052, IRON, f'{cols} by {rows} steel grid')
    if not lod and cols > 1:
        # Separate projecting central meeting edge is visible in both the detail and street exposure.
        u = (x0g + x1g) / 2
        solid(box(u - .005, z0g, u + .005, z1g), inset + .012, inset + .019, CASE, 'central meeting edge')

    if style in ('ground', 'base'):
        return
    ornamental = style in ('triangle', 'segment')
    plain = style in ('plain', 'paired-plain', 'ground-plain', 'court-plain')
    side = .235 if ornamental else (.105 if style in ('flat-apron','top-apron') else 0.)
    if side:
        strip([box(x0 - side*w, lo, x0, hi), box(x1, lo, x1 + side*w, hi)],
              -.062*w, .012, STONE, 'stone jamb faces')
    sill_front = -.16*w if ornamental else -.105*w
    lip = .085*w if ornamental else .055*w
    # The shared head and sill of a photographed pair meet halfway across its intervening brick pier.
    end0, end1 = opening.get('sill_ends', (x0-lip, x1+lip))
    solid(box(end0,lo-.105*w,end1,lo), sill_front, .018, STONE, 'projecting window sill')
    if not lod:
        solid(box(end0,lo-.031*w,end1,lo-.008*w), sill_front-.014, sill_front, EDGE, 'sill drip arris')
    if style in ('triangle','segment','flat-apron','top-apron','court-short-apron'):
        tail = .63 if ornamental else (.43 if style == 'top-apron' else .24)
        drop = min(tail*w, lo - float(opening.get('apron_floor', -1e4)))
        if drop > .1*w:
            z = lo-.10*w
            apron = Polygon([(c-.51*w,z), (c+.51*w,z), (c+.51*w,z-.76*drop),
                             (c+.33*w,z-.76*drop),(c+.33*w,z-drop),(c-.33*w,z-drop),
                             (c-.33*w,z-.76*drop),(c-.51*w,z-.76*drop)])
            solid(apron,-.052*w,.013,STONE,'stepped sill apron')
    if plain:
        head0, head1 = opening.get('head_ends', (x0-.10*w,x1+.10*w))
        solid(box(head0,hi,head1,hi+.16*w),-.044*w,.02,STONE,'plain stone lintel')
        return
    if not ornamental:
        length = .65
        solid(box(c-length*w, hi, c+length*w, hi+.130*w), -.095*w, .012, STONE, 'dressed flat head')
        solid(box(c-(length+.055)*w, hi+.130*w, c+(length+.055)*w, hi+.235*w),
              -.19*w,.010,EDGE,'head cap')
        return
    # The shadowed soffit is broken at the central keystone on Qiao's 920×614 detail.
    solid(detail([(-.735,0),(.735,0),(.735,.50),(-.735,.50)]),-.069*w,.016,STONE,'head face')
    for sign, label in ((-1,'left'),(1,'right')):
        def wing(coords):
            return detail([(sign*u,v)for u,v in coords])
        solid(wing([(.225,.218),(.787,.218),(.787,.275),(.876,.340),(.876,.401),(.244,.401)]),
              -.157*w,-.067*w,SHADE,label+' bed mould')
        solid(wing([(.232,.408),(.891,.408),(.891,.504),(.254,.504)]),
              -.206*w,-.067*w,EDGE,label+' broken cornice')
    steps = 18 if lod else 34
    outer = _pediment_outline(style,1.02,.55,.57,steps)
    lowest = [(-1.02,.52),(1.02,.52)]
    tympanum = detail(lowest+list(reversed(outer)))
    solid(tympanum,-.105*w,.005,STONE,'pediment tympanum')
    inner = _pediment_outline(style,.904,.455,.566,steps)
    band = detail(outer+list(reversed(inner)))
    solid(band,-.204*w,-.102*w,EDGE,'circular crown rim' if style=='segment' else 'raking crown rim')
    key = [(-.157,.80),(.157,.80),(.060,-.006),(-.052,-.006)]
    solid(detail(key),-.215*w,-.104*w,STONE,'tapered central key')
    if not lod:
        ridge = _pediment_outline(style,.948,.505,.555,steps)
        inset_band = detail(ridge+list(reversed(inner)))
        solid(inset_band,-.222*w,-.204*w,SHADE,'inner crown fillet')

def add_panel_links(b, face, openings, layout, lod=False):
    """Continuous dressed-stone panels identified between the second and third storeys."""
    if face not in ('north','street','front','court','south','courtyard','rear'):
        return
    lower={o['axis']:o for o in openings if o.get('level')==2}
    for upper in openings:
        if upper.get('level')!=3 or 'backing_span' not in upper:
            continue
        lo=lower.get(upper['axis'])
        if lo is None:
            continue
        x0,x1=upper['backing_span']
        # Ends meet the upper ground-floor belt and the underside of the separate window order.
        panel=box(x0,4.107,x1,upper['head']+.012)
        apertures=[box(o['center']-o['width']/2-.0015,o['sill']-.0015,
                       o['center']+o['width']/2+.0015,o['head']+.0015) for o in (lo,upper)]
        geom=panel.difference(unary_union(apertures))
        sign,point=_depth_mapper(face,upper,layout)
        d0,d1=sorted((-.030*sign,.016*sign))
        b.prism(geom,d0,d1,lambda t,z,v:point(t,sign*v,z),STONE,
                f"Hospital {upper['id']} | continuous stone-faced wall panel")
