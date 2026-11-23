"""Fixed grille, arched reveal, number plates and east end sash at No. 2 Yanqing Road.

The outlines refer to native pixels in Fayhoo's 2144 by 1424 photograph. The
wall intersection is evaluated for the actual depth of each layer. The artwork
and bars are modelled in geometry and contain no image from the photograph.
"""
from math import cos, pi, sin
from pathlib import Path
import sys

from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient

sys.path.append(str(Path(__file__).resolve().parents[1] / 'measurements'))
from register_front import Camera

GREEN = 'Yanqing 2 | deep green painted grille'
ENAMEL = 'Yanqing 2 | green enamel number plates'
WHITE = 'Yanqing 2 | ivory enamel lettering'
STONE = 'Yanqing 2 | pale entrance surround'
DARK = 'Yanqing 2 | shaded entrance reveal'
STEEL = 'Yanqing 2 | dark narrow steel casement'
GLASS = 'Yanqing 2 | shaded east sash glazing'
CALL = 'Yanqing 2 | pale door intercom'
INSERT = 'Yanqing 2 | graphite intercom inset'


def finish(rgb, roughness, metallic=0.0):
    def linear(v):
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    return {'color': [linear(v) for v in rgb], 'roughness': roughness, 'metallic': metallic}


PALETTE = {
    GREEN: finish((.15, .28, .235), .58, .19),
    ENAMEL: finish((.105, .34, .27), .43, .18),
    WHITE: finish((.80, .84, .73), .43),
    STONE: finish((.76, .75, .64), .85),
    DARK: finish((.12, .14, .13), .99),
    STEEL: finish((.16, .175, .165), .64, .28),
    GLASS: finish((.197, .207, .193), .32, .12),
    CALL: finish((.70, .71, .64), .53, .2),
    INSERT: finish((.17, .176, .164), .6, .14),
}

# The left top corner of the end sash lies behind a modern air conditioner.
# The visible transom and sill define its outer rectangular opening.
END_WINDOW = [(1739.5, 972.4), (1779.1, 972.5), (1783.3, 1067.0), (1743.6, 1067.1)]


def arch_points(cx, spring, radius_x, rise, bottom, samples=32):
    crown = [(cx + radius_x*cos(pi*i/samples), spring - rise*sin(pi*i/samples))
             for i in range(samples + 1)]
    return [(cx-radius_x, bottom), (cx+radius_x, bottom), *crown]


def wall_shape(shape, wall, depth):
    def ring(seq):
        points = [wall((u, v), depth) for u, v in seq]
        return [(float(p[0]), float(p[2])) for p in points]
    return orient(Polygon(ring(shape.exterior.coords), [ring(r.coords) for r in shape.interiors]), 1)


def openings(layout=None):
    """Return each wall depth and its exact cut polygon in facade X,Z metres."""
    layout = layout or {}
    wall = layout.get('wall') or Camera().wall
    gate_y = layout.get('gate_y', 0.)
    sash_y = layout.get('right_wall_y', 2.40)
    hole = Polygon(arch_points(1196.4, 1092., 48., 32.0, 1264.2))
    return {'gate': (gate_y, wall_shape(hole, wall, gate_y)),
            'right_window': (sash_y, wall_shape(Polygon(END_WINDOW), wall, sash_y))}


class PhotoJoinery:
    def __init__(self, builder, wall):
        self.builder = builder
        self.wall = wall

    def plate(self, shape, front, back, material, name):
        poly = wall_shape(shape, self.wall, front)
        self.builder.prism(poly, 0., back-front, lambda x, z, depth: (x, back-depth, z),
                           material, name)

    def rect(self, x0, y0, x1, y1, front, back, material, name):
        self.plate(box(x0, y0, x1, y1), front, back, material, name)


def grille(j, y, lod):
    front, back = y-.082, y-.053
    def bar(box_pixels, name, step=0):
        j.rect(*box_pixels, front+step, back+step, GREEN, 'No. 2 grille | '+name)

    # Left and right sidelights share the tall fixed frame. The hinged centre
    # leaf starts below the rectangular overlight.
    for x, label in ((1127.4, 'west outer upright'), (1267.7, 'east outer upright')):
        bar((x-1.5, 1035.6, x+1.5, 1264.0), label)
    for v, label, thickness in ((1036.7, 'outer head', 2.8), (1072.9, 'transom', 3.5),
                                (1262.3, 'low rail', 2.3)):
        bar((1128.8, v-thickness/2, 1266.3, v+thickness/2), label)
    for index, x in enumerate((1137.3, 1145.8, 1154.5, 1163.0, 1171.3, 1180., 1188.5,
                               1197.1, 1206., 1214.8, 1223.9, 1232.5, 1241.2, 1250.2, 1258.6)):
        bar((x-.88, 1038.1, x+.88, 1071.1), f'overlight vertical {index+1:02d}', .007)
    for x, label in ((1146.4, 'west leaf stile'), (1238.4, 'east leaf stile')):
        bar((x-1.35, 1074.6, x+1.35, 1261.1), label, -.008)
    for v, label in ((1078.1, 'leaf top'), (1147.4, 'upper subdivision'),
                     (1189.4, 'lower subdivision'), (1257.6, 'leaf bottom')):
        bar((1147.7, v-1.3, 1237.1, v+1.3), label, -.008)

    verticals = (1153., 1157.7, 1162.2, 1166.8, 1171.2, 1176., 1180.4, 1185.,
                 1189.7, 1194.1, 1198.9, 1203.6, 1208.1, 1212.8, 1217.3, 1222.,
                 1227.0, 1232.2)
    for zone, lo, hi in (('upper', 1079.3, 1146.0), ('lower', 1190.7, 1256.3)):
        for index, x in enumerate(verticals):
            bar((x-.71, lo, x+.71, hi), f'{zone} leaf rod {index+1:02d}', .001)
        # Short angular links alternating against the closely spaced uprights
        # are legible in the unobstructed bottom of the 2015 leaf.
        if not lod:
            for index, x in enumerate((1153., 1176., 1198.9, 1222.)):
                bar((x,lo+2.3,x+9.1,lo+3.9),f'{zone} top square link {index+1}', .001)
                bar((x,hi-3.9,x+9.1,hi-2.3),f'{zone} bottom square link {index+1}', .001)
    for side, x0, x1, rods in (('west',1129.,1145.,(1132.,1136.2,1141.2)),
                               ('east',1240.,1266.2,(1244.7,1249.4,1254.1,1258.6,1263.2))):
        for zone, lo, hi in (('upper',1074.6,1147.4),('lower',1190.6,1256.0)):
            for i,x in enumerate(rods):
                bar((x-.7,lo,x+.7,hi),f'{side} fixed {zone} rod {i+1}',.01)
        bar((x0,1255.9,x1,1258.1),side+' fixed bottom bar')
    for i,v in enumerate((1151.7,1156.5,1161.5,1166.5,1171.5,1176.5,1181.4,1186.3)):
        for label,x0,x1 in (('west',1129.0,1145.0),('leaf',1147.8,1215.7),('east',1261.6,1266.0)):
            bar((x0,v-1.03,x1,v+1.03), f'{label} midrail slat {i+1}',.002)
    bar((1215.2,1147.,1261.7,1189.2), 'solid lock and intercom apron',.007)
    bar((1243.,1118.,1258.,1155.8), 'intercom mount',-.009)
    j.rect(1243.3,1119.1,1254.5,1147.2,front-.030,front-.007,CALL,'No. 2 | pale intercom')
    for name, coords in (('speaker',(1245.0,1121.0,1252.5,1125.0)),
                         ('dark screen',(1245.0,1127.2,1252.4,1130.4)),
                         ('lower latch',(1244.1,1150.1,1254.0,1153.8))):
        j.rect(*coords,front-.0315,front-.029,INSERT,'No. 2 | intercom '+name)
    if lod:
        return
    for i in range(3):
        for k in range(3):
            x,v=1245.4+2.15*i,1132.8+2.55*k
            j.rect(x,v,x+1.15,v+1.25,front-.032,front-.030,INSERT,f'No. 2 | intercom key {i+1}-{k+1}')


def address(j, centre, w, h, y, label):
    x,v=centre
    def point(a,b):
        return (x+w*a, v+h*b)
    j.plate(box(x-w/2,v-h/2,x+w/2,v+h/2).buffer(.38,quad_segs=3),
            y-.013,y-.003,ENAMEL,label+' | green enamel')
    path=[(-.095,-.232),(-.064,-.319),(-.005,-.348),(.061,-.315),(.081,-.222),
          (.062,-.149),(-.080,.050),(-.085,.090),(.095,.090)]
    numeral=LineString([point(a,b) for a,b in path]).buffer(w*.035,quad_segs=4)
    j.plate(numeral,y-.016,y-.013,WHITE,label+' | original numeral 2')
    # Three small white character groups resolve on each plate; individual
    # strokes cannot reliably be transcribed in this exposure.
    for i,u in enumerate((-.241,0,.241)):
        a,b=point(u-.028,.270);c,d=point(u+.028,.325)
        j.rect(a,b,c,d,y-.0148,y-.013,WHITE,label+f' | small address line {i+1}')


def end_window(j, y):
    def uv(s,t):
        a,b,c,d = END_WINDOW
        return tuple((1-t)*(a[i]*(1-s)+b[i]*s)+t*(d[i]*(1-s)+c[i]*s) for i in (0,1))
    def pane(s0,t0,s1,t1):
        return Polygon([uv(s0,t0),uv(s1,t0),uv(s1,t1),uv(s0,t1)])
    j.plate(pane(.025,.014,.975,.988),y+.093,y+.110,GLASS,'No. 2 east end | seven visible dark glazing fields')
    frame=Polygon(END_WINDOW).difference(pane(.032,.016,.969,.985))
    j.plate(frame,y+.055,y+.092,STEEL,'No. 2 east end | steel sash perimeter')
    j.plate(pane(.476,.016,.512,.985),y+.065,y+.088,STEEL,'No. 2 east end | centre mullion')
    for i,t in enumerate((.247,.476,.712)):
        j.plate(pane(.03,t-.008,.971,t+.008),y+.064,y+.088,STEEL,f'No. 2 east end | transom {i+1}')
    sill=Polygon([(1733.3,1068.1),(1795.8,1068.1),(1796.2,1079.2),(1733.6,1079.2)])
    head=Polygon([(1732.4,961.1),(1789.0,961.4),(1789.2,972.8),(1732.8,972.5)])
    j.plate(sill,y-.102,y+.011,STONE,'No. 2 east end | projecting sill')
    j.plate(head,y-.068,y+.012,STONE,'No. 2 east end | pale head')


def add_entry(b, lod=False, layout=None):
    """Add the built-in entrance and east number/window. Depth grows indoors."""
    layout=layout or {}
    j=PhotoJoinery(b,layout.get('wall') or Camera().wall)
    for material, spec in PALETTE.items():
        b.palette.setdefault(material,spec)
    y=layout.get('gate_y',0.)
    sy=layout.get('right_wall_y',2.40)
    inner=Polygon(arch_points(1196.4,1092.,48.,32.,1264.2))
    outer=Polygon(arch_points(1196.4,1091.6,56.5,43.6,1264.2))
    j.plate(outer.difference(inner), y-.023,y+.014,STONE,'No. 2 | arched entrance surround')
    j.plate(Polygon([(1184.4,1015.6),(1208.,1016.2),(1205.4,1035.6),(1187.2,1035.3)]),
            y-.043,y+.006,STONE,'No. 2 | high trapezoidal keystone')
    if layout.get('backing',True):
        depth=layout.get('recess_depth',.31)
        j.plate(inner.buffer(1.0),y+depth,y+depth+.015,DARK,'No. 2 | shaded end of observed entrance')
    grille(j,y,lod)
    address(j,(1111.7,1096.8),19.2,15.2,y,'No. 2 entrance plate')
    address(j,(1841.9,1076.4),16.2,13.5,sy,'No. 2 east plate')
    end_window(j,sy)
