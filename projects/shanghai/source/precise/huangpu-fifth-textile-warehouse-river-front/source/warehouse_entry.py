"""South Suzhou Road 1295, photographed entrance in the November 2020 street view.

The cut in the main masonry belongs to the caller. Width and wall-face heights
follow the rectified photograph. The set-back door depth models the visible
first bay; no plan survey or interior fit-out is implied.
"""
from functools import lru_cache
from pathlib import Path

from shapely import affinity
from shapely.geometry import box as rect
from shapely.ops import unary_union

from sign_lettering import lettering_shapes


def _finish(rgb, roughness, metallic=0.0):
    def linear(v):
        s = v / 255.0
        return s / 12.92 if s <= .04045 else ((s + .055) / 1.055) ** 2.4
    return dict(color=[linear(c) for c in rgb], roughness=roughness, metallic=metallic)


STONE = 'Portal pale cast stone'
LIP = 'Portal inset stone bevel'
MORTAR = 'Glass block cement joint'
BLOCK = 'Square glass pale grey green'
FACET = 'Pressed glass facet'
METAL = 'Vestibule bronze frame'
GLASS = 'Setback dark glazing'
FLOOR = 'Grey vestibule threshold'
LETTERS = 'Oxide red projecting letters'
ROOF = 'Faded grey gable lettering'
GREEN = 'Green enamel address plaques'
WHITE = 'Enamel off white type'
DARK = 'Square brown tenant plate'
PALETTE = {
    STONE: _finish((192, 186, 170), .83), LIP: _finish((152, 148, 132), .79),
    MORTAR: _finish((155, 156, 139), .81), BLOCK: _finish((174, 181, 160), .31, .10),
    FACET: _finish((149, 159, 138), .29, .14), METAL: _finish((95, 91, 78), .45, .43),
    GLASS: _finish((45, 52, 46), .29, .28), FLOOR: _finish((128, 130, 119), .74),
    LETTERS: _finish((110, 60, 46), .61, .30), ROOF: _finish((165, 162, 149), .78),
    GREEN: _finish((37, 102, 85), .53, .16), WHITE: _finish((218, 218, 195), .60),
    DARK: _finish((99, 79, 66), .69),
}
FONT = Path(__file__).with_name('entry_letters') / 'RiverFrontEntry.otf'


@lru_cache(maxsize=28)
def _letters(text, width, height, lod):
    shapes = [g for _, g in lettering_shapes(text, width, height, font=FONT)]
    # Keep the letter counters open in both public models.
    return unary_union(shapes).simplify(height * (.012 if lod else .003),
                                        preserve_topology=True)


def _word(f, text, x, z, w, h, back, front, material, label, lod):
    outline = affinity.translate(_letters(text, w, h, bool(lod)), xoff=x, yoff=z)
    f.prism(outline, back, front, material, label)


def roof_letters(facade, d, lod, x, z, width, height, depth):
    """Place one faded word on the caller's top signboard, centered at (x,z)."""
    _word(facade, 'UVWORKING', x, z, width, height, depth, depth+.009,
          ROOF, 'Gable weathered type', lod)


def entry_ground(d):
    """Return model-space x and inward distances relative to the street wall."""
    cut = d['street']['portal']
    limits = [cut['center']-cut['width']/2, cut['center']+cut['width']/2]
    return dict(clear_x=limits, interior_depth_m=[0.0, 1.25], sill_m=cut['sill'],
                head_m=cut['head'], modeled_door_depth_m=1.49,
                true_opening=True, positive_depth='inside')


def _inverted_u(x, halfwidth, top, inner_halfwidth, inner_top):
    return rect(x-halfwidth, .0, x+halfwidth, top).difference(
        rect(x-inner_halfwidth, -.02, x+inner_halfwidth, inner_top))


def _block(f, x, z, w, h, lod):
    # One physically separate square, with a raised face and four sloped bevels.
    rear = .151
    front = .205
    inset = min(w, h) * .11
    bevel = .014
    rings = [(w/2, h/2, rear), (w/2, h/2, front-bevel),
             (w/2-inset, h/2-inset, front)]
    vertices = [f.point(x+sx*hw, z+sz*hh, depth)
                for hw, hh, depth in rings
                for sx, sz in [(-1,-1), (1,-1), (1,1), (-1,1)]]
    faces = [(3,2,1,0), (8,9,10,11)]
    for start in (0,4):
        for j in range(4):
            k = (j+1)%4
            faces.append((start+j,start+k,start+k+4,start+j+4))
    f.builder.add(vertices, faces, BLOCK, f.label+'/Pressed glass blocks')
    if not lod:
        # Diagonal facet behind the glossy face is represented by shallow relief.
        shape = [(x-w*.31,z-h*.25),(x-w*.20,z+h*.24),(x+w*.20,z+h*.26),
                 (x+w*.08,z+h*.11),(x-w*.16,z+h*.09)]
        from shapely.geometry import Polygon
        f.prism(Polygon(shape), front+.001, front+.004, FACET, 'Pressed glass facets')


def _portal(f, d, lod):
    cut = d['street']['portal']
    x, w, head, sill = (cut[key] for key in ('center','width','head','sill'))
    s = w / 2.35828
    inner = w/2
    # The three consecutive materials are visible across the jamb and above the head.
    jamb = inner+.100*s
    inner_glass = jamb+.113*s
    block = .215*s
    outer_glass = inner_glass+block
    glass_start = head+.203*s
    top = glass_start+block
    outer = inner+.99*s
    f.prism(_inverted_u(x,outer, head+1.025*s, outer-.082*s, head+.94*s),
            -.012,.259, LIP, 'Stone outside bead')
    f.prism(_inverted_u(x,outer-.082*s, head+.94*s, outer_glass, top),
            -.012,.232, STONE, 'Broad squared stone portal')
    f.prism(_inverted_u(x,inner_glass,glass_start, jamb,head+.092*s),
            -.014,.200, LIP, 'Inner sandstone return')
    f.prism(_inverted_u(x,jamb,head+.092*s,inner,head),
            -.019,.245, STONE, 'Raised inner jambs')
    f.prism(_inverted_u(x,outer_glass,top,inner_glass,glass_start),
            -.015,.150, MORTAR, 'Glass block bedding')
    cols = round(2*inner_glass/block)
    rows = round(glass_start/block)
    dx, dz = 2*inner_glass/cols, glass_start/rows
    gap = .012*s
    for sign in (-1,1):
        bx = x+sign*(inner_glass+block/2)
        for row in range(rows):
            _block(f,bx,(row+.5)*dz,block-gap,dz-gap,lod)
        _block(f,bx,glass_start+block/2,block-gap,block-gap,lod)
    for col in range(cols):
        _block(f,x-inner_glass+(col+.5)*dx,glass_start+block/2,dx-gap,block-gap,lod)

    reach = 1.49
    for sign in (-1,1):
        f.box(x+sign*(inner+.026), (head+sill)/2, .052, head-sill,
              reach, -reach/2, LIP, 'Vestibule returns')
    f.box(x,head+.027,w,.054,reach,-reach/2,LIP,'Vestibule soffit')
    f.box(x,sill-.031,w,.062,reach+.16,-(reach-.16)/2,FLOOR,'Entrance floor')
    f.box(x,(head+sill)/2,w,head-sill,.038,-reach-.019,GLASS,'Setback door glazing')
    for u in (x-inner+.025, x, x+inner-.025):
        f.box(u,(head+sill)/2,.042,head-sill,.048,-reach+.017,METAL,'Setback metal stiles')
    f.box(x,head-.44*s,w,.043,.048,-reach+.017,METAL,'Door transom')
    if not lod:
        for sign in (-1,1):
            f.box(x+sign*.088, sill+.95,.019,.36,.070,-reach+.047,METAL,'Door pulls')
    # The photograph shows free-standing letter contours, supported at the sill.
    baseline = d['portal_board_height']-.631*s
    _word(f,'UVWORKING',x,baseline+.200*s,4.11*s,.400*s,.294,.357,
          LETTERS,'Red projecting entry type',lod)
    f.box(x,baseline-.018,4.23*s,.034,.095,.256,LIP,'Sign mounting rail')


def _plates(f, d, lod):
    distance = d['pillar_distance']
    for side in (-1,1):
        x = side*distance/2
        z = 2.30 if side<0 else 2.28
        f.box(x,z,.374,.225,.035,.181,GREEN,'Enamel street number plaques')
        _word(f,'1295',x,z+.029,.277,.111,.199,.205,WHITE,'Street number',lod)
        _word(f,'南苏州路',x,z-.065,.244,.043,.199,.203,WHITE,'Street name',lod)
        # The left stone commemorative tablet is visible but unreadable at this scale.
        f.box(x,z-.397,.619,.503,.049,.184,STONE if side<0 else DARK,'Lower wall plaques')
        if side>0:
            border = rect(x-.190,z-.57,x+.190,z-.224).difference(
                rect(x-.182,z-.562,x+.182,z-.232))
            f.prism(border,.210,.215,WHITE,'Tenant plaque perimeter')
            _word(f,'UV',x,z-.352,.240,.129,.210,.216,WHITE,'Tenant monogram',lod)


def install(facade, d, lod):
    _portal(facade,d,lod)
    _plates(facade,d,lod)
    return entry_ground(d)
