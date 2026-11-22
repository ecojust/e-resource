"""The two pierced bronze door panels at 181 East Nanjing Road.

The local drawing grid runs left to right and top to bottom as seen from the
pavement. Each 100 × 100 grid fills 0.66 × 0.81 m. The photographs were used to
draw the silhouettes. No photographic material or solid rectangular backing is
used. The open areas reveal the recessed door behind them.
"""
import math

from shapely import affinity, set_precision
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union


BRONZE = 'patinated bronze'
LIGHT = 'raised bronze highlights'
WIDTH, HEIGHT = .66, .81
FRAME = Polygon([(9, 0), (91, 0), (100, 11), (100, 87), (93, 100),
                 (7, 100), (0, 87), (0, 11)])
INNER = FRAME.buffer(-4.0, join_style=2)


class Panel:
    def __init__(self, face, x, z, side, distant):
        self.face = face
        self.x = x
        self.z = z
        self.side = side
        self.distant = distant

    def cast(self, outline, back, front, material, name):
        if outline.is_empty:
            return
        # Clipping a scroll against the frame can leave coincident vertices a
        # few ULPs apart. Resolve those in the panel drawing before translating
        # it to either door leaf; the snapping grid is under 0.02 mm wide.
        outline = set_precision(outline, .002)
        shape = affinity.affine_transform(outline, [WIDTH / 100, 0, 0, -HEIGHT / 100,
                                                    self.x - WIDTH / 2, self.z + HEIGHT / 2])
        self.face.prism(shape, back, front, material, self.side + ' panel ' + name)

    def line(self, points, width, back, front, material, name):
        strip = LineString(points).buffer(width / 2, resolution=2, cap_style=2, join_style=2)
        self.cast(strip.intersection(INNER), back, front, material, name)

    def ribs(self, paths, width, back, front, material, name):
        lines = [LineString(path).buffer(width / 2, resolution=2, join_style=1) for path in paths]
        self.cast(unary_union(lines).intersection(INNER), back, front, material, name)

    def relief(self, sections, back, high, name, material=BRONZE):
        """Cast a closed oval-section ridge along a drawn limb or fold.

        Each section gives x, y and apparent half-width in drawing units.
        Tangents and widths are calculated in metres so the relief remains
        round in cross-section when the drawing grid is stretched vertically.
        """
        if not self.distant and len(sections) >= 3:
            # A short cardinal interpolation rounds the shoulder, knee and calf
            # without changing the measured end points of each silhouette.
            rounded = []
            for i, a in enumerate(sections[:-1]):
                before = sections[max(0,i-1)]
                b = sections[i+1]
                after = sections[min(i+2,len(sections)-1)]
                middle = tuple(.5*(a[k]+b[k]) + .045*((b[k]-before[k])-(after[k]-a[k]))
                               for k in range(3))
                rounded.extend((a, middle))
            sections = rounded+[sections[-1]]
        centers = [(self.x+(x-50)*WIDTH/100, self.z+(50-y)*HEIGHT/100)
                   for x, y, _ in sections]
        max_width = max(s[2] for s in sections) * WIDTH/100
        sides = 6 if self.distant else 10
        vertices, faces = [], []
        for i, ((x, z), (_, _, r)) in enumerate(zip(centers, sections)):
            prev = centers[max(0, i-1)]
            nxt = centers[min(len(centers)-1, i+1)]
            dx, dz = nxt[0]-prev[0], nxt[1]-prev[1]
            length = math.hypot(dx, dz)
            width = r*WIDTH/100
            thick = (high-back) * min(1, width/(max_width*.7))
            for k in range(sides):
                angle = math.tau*k/sides
                offset = width*math.cos(angle)
                depth = back+thick*(1+math.sin(angle))/2
                vertices.append(self.face.point(x+offset*(-dz)/length,
                                                z+offset*dx/length, depth))
            if i:
                for k in range(sides):
                    a=(i-1)*sides+k
                    b=(i-1)*sides+(k+1)%sides
                    faces.append((a, b, b+sides, a+sides))
        faces.append(tuple(reversed(range(sides))))
        last = (len(sections)-1)*sides
        faces.append(tuple(last+k for k in range(sides)))
        # (u, z, depth) is right-handed on a Facade; these ring windings
        # give outward normals for the above choice of section left normal.
        self.face.builder.add(vertices, faces, material, self.side+' panel '+name)

    def lambent_bands(self, paths, name):
        for i, path in enumerate(paths):
            self.relief(path, .088, .1115, name+' '+str(i+1), LIGHT)


def octagonal_border(p):
    p.cast(FRAME.difference(INNER), .045, .078, BRONZE, 'clipped-corner frame')
    if not p.distant:
        band = FRAME.buffer(-1.15, join_style=2)
        p.cast(band.difference(band.buffer(-.66, join_style=2)), .076, .085,
               LIGHT, 'raised perimeter bead')
    # Both originals stand on an irregular, continuous low plinth.
    plinth = Polygon([(4,94), (10,90.5), (18,91.4), (24,89.7), (31,91.2),
                      (36,89.7), (41,90.2), (48,88.2), (54,90.3), (60,89.7),
                      (65,91.1), (73,90.5), (79,88.6), (84,88.1), (90,90.4),
                      (95,94.9), (92,98), (8,98)])
    p.cast(plinth.intersection(INNER), .056, .082, BRONZE, 'ground under feet')


def storm(p):
    # Four angular shafts cross the open ground at different inclinations.
    bolts = [[(3,23.4),(26,20.4),(17.5,18.2),(43.2,17.2),(35.3,15.8),
              (61,12.5),(53,15.2),(60.7,17.3),(40,19.1),(45.3,20.5),(3,25.1)],
             [(4,69.8),(27,56.3),(20,56.4),(39.2,46.1),(33,47),
              (77,24.1),(76,26.2),(80.7,26.5),(47.2,44.2),(49.1,45.2),
              (32.5,53.8),(38,53.8),(4,71.7)],
             [(41.1,91.2),(54,73.2),(46.8,76.3),(65.8,54.1),(61.3,56.6),
              (87.4,31.4),(82.4,40.1),(86.8,38.1),(68.3,57.3),(72.9,55.5),
              (53.8,78.4),(57.4,76.1),(44.3,92)],
             [(67,54.4),(71.1,45.2),(69.5,46.5),(84.7,26.9),(82.6,31.7),
              (85.2,30.1),(73.3,47.2),(75.2,46.2)]]
    p.cast(unary_union([Polygon(b) for b in bolts]).intersection(INNER),
           .048, .065, BRONZE, 'forked lightning')
    arcs=[]
    # The near lobe covers the two curls farther back. Trim the hidden arcs
    # before casting to preserve the three silhouettes at the upper corner.
    closer = Polygon()
    for x,y,r in [(102,16,11.5),(99,13,18.8),(88.0,-2.5,19.0)]:
        disk=Point(x,y).buffer(r, resolution=9 if p.distant else 18)
        for inset in ([0] if p.distant else [0,2.05,4.0,6.0]):
            ring=disk.buffer(-inset)
            arcs.append(ring.difference(ring.buffer(-1.05)).difference(closer))
        closer=closer.union(disk)
    p.cast(unary_union(arcs).intersection(INNER),.054,.071,LIGHT,'upper storm scrolls')


def sun(p):
    # The solar disk meets the top and left borders. A broad fluted ring and
    # four clearly separated beams fan down and to the right behind the figure.
    inner=Point(2.5,-.6).buffer(24, resolution=12 if p.distant else 25)
    outer=Point(2.5,-.6).buffer(36.6, resolution=15 if p.distant else 28)
    p.cast(inner.intersection(INNER),.049,.068,BRONZE,'sun disk')
    corona=outer.difference(inner.buffer(1.2))
    p.cast(corona.intersection(INNER),.049,.068,BRONZE,'solar rim')
    rays=[[(34.8,12.8),(96,22.2),(96,30.1),(35,16.6)],
          [(33,19.1),(96,37.2),(96,43.1),(32.3,21.5)],
          [(29,26.2),(94.7,83.2),(91.6,92),(23.7,29.5)],
          [(21,33),(41.4,93),(35.1,94.1),(17.6,34.4)]]
    p.cast(unary_union([Polygon(r) for r in rays]).intersection(INNER),
           .049,.065,BRONZE,'four open solar beams')
    if p.distant:
        p.cast(outer.difference(outer.buffer(-1.1)).intersection(INNER),
               .066,.075,LIGHT,'edge of solar rim')
        return
    ribs=[]
    for r in (25.5,30.3,36):
        d=Point(2.5,-.6).buffer(r,resolution=25)
        p.cast(d.difference(d.buffer(-.61)).intersection(INNER),.066,.075,LIGHT,'raised solar ring')
    def on_ring(radius, degrees):
        angle=math.radians(degrees)
        return (2.5+radius*math.cos(angle),-.6+radius*math.sin(angle))
    # The outer corona is chased in two staggered rows. Each scallop has
    # its own curved light-catching lip; the joints do not form square cells.
    for row, (radius, phase) in enumerate([(26.6,1.1),(31.3,-2.5)]):
        for i in range(12):
            start=phase+i*8.3+(.29,-.16,.25,-.12)[i%4]
            end=start+7.65
            mid=(start+end)*.5
            rim=[on_ring(radius+.08,start),on_ring(radius+.21,mid-1.1),
                 on_ring(radius+.63,mid+1.0),on_ring(radius+.34,end-.6),
                 on_ring(radius+3.8,end)]
            p.line(rim,.56,.068,.075+(i%3)*.00032,LIGHT,'chased solar blocks')
    for j, ray in enumerate(rays):
        a,b,c,d=ray
        for k in (.25,.62):
            ribs.append([((1-k)*a[0]+k*d[0],(1-k)*a[1]+k*d[1]),
                         ((1-k)*b[0]+k*c[0],(1-k)*b[1]+k*c[1])])
    p.ribs(ribs,.56,.065,.074,LIGHT,'sunburst fluting')
    waves=[[(x+1,y),(x+3.2,y+.4),(x+4.6,y+1.6),(x+6.6,y+2.0),(x+8.3,y+1.4)]
           for x,y in [(8,5),(13,7.8),(4.9,10.1),(11,13.2),(4,16.3),(6,20.4),(17.1,10.2)]]
    p.ribs(waves,.85,.066,.078,LIGHT,'ripples on the disk')


def left_worker(p):
    storm(p)
    p.line([(12.3,35.6),(57.1,6.9)],2.0,.065,.083,BRONZE,'diagonal hammer shaft')
    p.cast(Polygon([(4,31.3),(8.2,32.4),(12.9,37.2),(16.4,40.2),
                    (16.6,43.8),(12.1,46.6),(8.2,44.8),(3.5,41.4)]),
           .065,.092,BRONZE,'hammer head')
    limbs=[
      ('rear raised arm',[(66.8,28,3.4),(72.2,20.8,3.4),(73.1,15.1,3.2),
                           (68.1,12.7,2.6),(62.2,10.2,2),(57.8,7.4,2.7)]),
      ('rear striding leg',[(53.5,54,5.1),(49.3,58.2,5.5),(44.4,64.2,4.9),(37.1,71.2,3.0),
                            (31.2,74.5,4.1),(26.8,78.1,3.0),(19.2,85.2,2.4),(15.7,89.2,1.7)]),
      ('rear foot',[(13.2,89.5,1.5),(16,90.1,2.2),(19.8,91.5,1.6),(24,92,.6)]),
      ('front bent leg',[(58.1,55.4,5.3),(64.4,58.2,5.0),(69.3,62.2,4.6),(73.7,65.8,3.4),
                          (71.3,69.4,3.0),(67,75.8,3.5),(63.3,82.9,2.2),(60.2,88.7,1.7)]),
      ('front foot',[(58.1,89.7,1.6),(61.2,90.5,2),(65.2,90.9,1.6),(69.2,90.8,.8)]),
      ('torso',[(54.9,55.2,5.0),(57.1,51,6.5),(57.7,46.2,7.3),(57.1,40.2,9.1),
                (57.5,35.1,10.2),(58.2,31.8,7.4),(60,29.5,3.5)]),
      ('hammer arm',[(49.5,32.7,4.2),(45.6,33.6,4.0),(42.3,36.0,3.8),(38.6,39.3,2.7),
                     (36.5,38.1,2.2),(34.8,34.5,2.7),(32.4,29.6,2.3),(30.9,26,1.7),(30,24,2.0)]),
      ('neck',[(58.6,31.5,3.2),(62,28.5,3.8),(64.4,25.2,2.7)]),
      ('inclined head',[(64.9,25.9,2.5),(65.8,23.8,4.1),(66.3,21.0,4.5),(65.8,18.8,4.0),
                        (65.4,17.6,2.2)])]
    for name,sections in limbs:
        p.relief(sections,.072,.105,name)
    p.cast(Polygon([(61,21),(61.8,18),(65.9,15.8),(69.2,16.3),(70.8,18.5),(70.3,20.2),
                    (68.8,19.8),(66.6,20.1),(64.1,22.4)]),.081,.106,BRONZE,'swept hair')
    p.cast(Polygon([(69.8,20.7),(69.6,22.3),(68.8,24.3),(67.5,24.7),(67.2,26.1),
                    (66.2,26.9),(64.8,26.2),(64.3,23.1)]),.084,.104,BRONZE,'face in profile')
    p.cast(Polygon([(50.7,50.6),(64.8,51.6),(64.3,54.5),(61,57.3),(57.8,61.0),
                    (53.7,59.2),(51.1,54.7)]),.079,.106,BRONZE,'pleated trunks')
    if p.distant:
        return
    p.relief([(53.0,8.3,.7),(54.0,7.0,1.7),(56.3,6.7,1.95),(58.2,7.9,1.2)],
             .082,.108,'upper gripping hand')
    p.relief([(27.1,23.8,.8),(28.0,23.5,1.9),(29.9,24.7,2.05),(31.4,26.5,1.1)],
             .082,.108,'lower gripping hand')
    p.relief([(48,35.5,.4),(50.4,34.5,2),(53.4,34.2,2.4),(56.4,36.3,1.8),(58.5,38.2,.5)],
             .083,.106,'near pectoral')
    p.relief([(59.4,33.3,.5),(61.8,35.5,2.55),(64.7,36.9,2.1),(66.1,36.2,.55)],
             .084,.107,'far pectoral')
    p.lambent_bands([
        [(48.3,37.1,.55),(51.1,35.9,1.55),(54.9,36.5,1.9),(58.1,38.7,.95),(60.1,39.4,.35)],
        [(59.6,35.4,.5),(62,37.5,1.3),(65.3,38.0,1.5),(67,36.2,.4)],
        [(39.2,37.1,.4),(41.9,35.4,1.4),(45.2,33.7,.55)],
        [(36.5,37.2,.4),(35.3,33.7,1.0),(32.9,28.1,.35)],
        [(47.6,59.8,.5),(46.2,62.3,1.8),(41.4,67.3,1.15),(38.2,70.2,.35)],
        [(33.5,73.8,.45),(30.8,75.5,1.4),(27.1,78.7,.4)],
        [(62.1,58.4,.6),(66.9,61.8,1.8),(71.0,63.8,.45)],
        [(70.8,68.3,.4),(68.3,73.3,1.15),(63.4,82.1,.35)]], 'modelled muscle')
    # The lower chest folds bow down to the right, then wrap the far side
    # of the trunk. Their heights and lengths vary from chest to waistband.
    chest=[
        [(49.1,39.0,.30),(51.0,38.7,.72),(53.0,39.0,1.05),(55.7,40.8,1.15),
         (58.4,42.2,1.30),(60.5,42.8,1.22),(62.4,42.6,.9),(64.2,41.4,.5),(65.3,42.8,.25)],
        [(49.5,41.1,.23),(51.5,40.9,.7),(53.8,41.8,.94),(56.4,43.35,1.02),
         (59.6,44.9,1.0),(62.0,45.0,.85),(63.8,44.16,.62),(65.0,43.0,.4),(66.1,44.25,.20)],
        [(49.6,44.1,.20),(52.2,44.5,.52),(54.4,45.5,.94),(57.5,46.55,1.08),
         (60.7,47.25,.98),(62.7,47.20,.82),(64.5,46.50,.46),(65.5,45.7,.23)],
        [(49.8,47.7,.27),(52.2,48.35,.7),(55.4,49.1,.82),(58.6,49.6,.77),
         (61.6,49.6,.58),(63.65,49.1,.4),(65.2,48.2,.24)]]
    for j, ridge in enumerate(chest):
        p.relief(ridge,.094,.114-j*.00075,'curved chest fold '+str(j+1),BRONZE)
    p.relief([(59.6,30.5,.3),(60.7,29.5,.73),(62.2,27.5,.8),(63.2,26.6,.25)],
             .089,.105,'turned neck tendon',LIGHT)
    p.ribs([[(52.3+i*2.2,51.9),(53.1+i*1.4,57.5)] for i in range(5)],
           .56,.104,.112,LIGHT,'pleats')
    p.ribs([[(62.2,19+i*.65),(65.5,17.0+i*.7),(68.6,17.1+i*.7)] for i in range(3)],
           .48,.104,.113,LIGHT,'hair divisions')
    p.ribs([[(27.6+i*.84,24.4),(29.9+i*.7,26.6)] for i in range(4)]+
           [[(53.9+i*.92,7),(55.6+i*.85,8.1)] for i in range(4)]+
           [[(67,21.8),(68.3,22.1)],[(67.1,25.0),(68.0,24.9)]],
           .43,.100,.115,LIGHT,'hands and brow')


def right_worker(p):
    sun(p)
    limbs=[
      ('bent standing leg',[(47.5,61.4,6.0),(41.8,62.8,5.2),(33.0,62.8,4.6),(23.7,63.9,3.9),
                             (20.6,66.7,3.2),(22.5,71.8,3.3),(24.3,79.2,2.6),(25.5,87.0,1.7)]),
      ('standing foot',[(26.1,88.2,1.6),(24.1,89.3,2.2),(20.1,90.0,1.5),(15.1,90.9,.65)]),
      ('folded leg on ground',[(53.9,61.9,6.0),(54,66.6,5.7),(53.2,73.8,4.8),(54,82.5,4.2),
                               (54.1,87.1,3.2),(57.5,89.4,2.6),(64.6,88.8,3.7),
                               (72.3,89.5,2.1),(80.4,90.7,1.4),(85.8,89.1,1.15)]),
      ('leaning torso',[(48,60.6,6.6),(48.9,55.4,7.3),(51.6,49.4,9.0),(55,43.0,9.8),
                        (59.9,39.1,6.5),(62.8,37.8,3.5)]),
      ('arm towards the sun',[(51.3,42.8,4.2),(46.6,39.0,3.8),(42.2,35.9,3.3),
                              (38.1,33.3,2.6),(35,29.8,2.3),(31.1,26.3,1.8),
                              (28.2,24.5,1.35),(24.1,22.5,1.0)]),
      ('folded forearm',[(61.2,42.5,4.5),(65.6,46.6,3.8),(69.4,51.4,3.15),
                         (72.9,55.7,2.5),(71.7,57.7,2.25),(67.0,55.4,2.05),
                         (62.8,51.2,1.6),(60.8,48.4,1.0)]),
      ('neck turned upwards',[(61.2,39.7,3.5),(62.6,36.8,4.2),(63.3,34.2,3.0)]),
      ('upturned head',[(61.6,35.5,2.7),(62.4,33.2,4.2),(64.6,30.4,5.0),
                        (66.0,29.2,3.8),(67.6,28.5,2.35)])]
    for name,sections in limbs:
        p.relief(sections,.072,.105,name)
    p.cast(Polygon([(58.7,34.1),(58.5,31.9),(59.9,30.9),(60.0,29.6),(62.4,29.1),
                    (63.5,27.8),(65,27.9),(64.7,31.5),(63.2,34.1)]),
           .078,.105,BRONZE,'raised profile and nose')
    p.cast(Polygon([(64,28),(66,25.9),(68.6,26.1),(71.9,27.9),(72.8,30.1),(71.8,32.8),
                    (69.1,35.1),(66.6,35.0),(65.8,32),(64.2,32.4)]),
           .086,.107,BRONZE,'swept hair')
    p.cast(Polygon([(42.5,56.1),(59.9,57.5),(59.2,60.5),(56,62),(50.4,66.1),
                    (45.4,69.1),(42.2,66.4),(41.5,62.8)]),.079,.105,BRONZE,'pleated trunks')
    if p.distant:
        return
    p.relief([(24.1,21.6,.55),(25.8,22.8,1.3),(28,23.6,1.65),(29.6,25.7,1)],
             .083,.107,'hand reaching for the disk')
    p.relief([(47.8,46.2,.5),(51.0,45.4,2.3),(55.8,42.6,3.0),(59.6,41.5,.7)],
             .083,.107,'near pectoral')
    p.relief([(61.3,43.0,.5),(62.9,44.7,1.6),(65.0,46.3,.6)],.085,.106,'raised shoulder')
    p.lambent_bands([
        [(48.2,46.6,.4),(52.4,45.8,1.25),(56.9,44.2,1.9),(60,42.1,.55)],
        [(44,36.4,.45),(40.9,34.8,1.6),(38.8,32.4,.42)],
        [(32.4,26.8,.45),(35,29.4,.9),(36.8,31.1,.35)],
        [(65.3,46.6,.45),(67.2,48.5,1.45),(69.8,52.2,.7)],
        [(24,64.1,.5),(29.2,62.2,1.4),(37.4,62.9,.5)],
        [(21.2,67.9,.5),(22.6,72.1,1.5),(24.8,84.7,.45)],
        [(51,65.6,.6),(51.3,69.5,2.2),(52.0,77.2,1.4),(53.8,84.1,.45)],
        [(54.2,67,.4),(55.1,71.5,1.3),(55.5,78.1,.45)],
        [(56.2,88.2,.55),(62.9,87.2,1.4),(69.1,88.3,.5)]], 'modelled muscle')
    right_chest=[
        [(48.0,48.55,.40),(50.1,49.25,.96),(52.9,49.68,1.15),(55.0,49.68,1.10),
         (57.9,49.10,.92),(59.9,48.2,.65),(61.35,47.70,.28)],
        [(46.6,51.30,.35),(48.4,52.15,.88),(51.3,52.55,1.03),(54.8,52.57,1.0),
         (56.6,52.29,.8),(58.9,51.60,.53),(60.2,50.9,.20)],
        [(45.4,54.20,.32),(47.4,55.0,.74),(50.6,55.7,.98),(53.8,55.86,1.04),
         (56.4,55.45,.74),(58.65,54.8,.47),(59.7,54.3,.18)],
        [(43.9,49.4,.23),(45.6,48.9,.61),(47.4,47.8,.67),(48.25,46.6,.32)],
        [(42.85,52.7,.2),(44.4,52.15,.64),(46.0,51.00,.76),(47.3,49.75,.35)],
        [(42.0,55.62,.18),(43.56,55.22,.58),(45.05,54.32,.64),(46.5,52.95,.30)]]
    for j,ridge in enumerate(right_chest):
        p.relief(ridge,.093,.1138-(j%3)*.0007,'inclined ribcage '+str(j+1),BRONZE)
    p.ribs([[(45.4+i*2.6,57.7),(43.1+i*1.05,65.1)] for i in range(5)],
           .61,.104,.113,LIGHT,'pleats')
    p.ribs([[(66.2+i*1.2,26.9+i*.23),(66.0+i*1.2,29.1+i*.4),(64.6+i*1.25,32.0+i*.32)]
            for i in range(5)],.57,.104,.115,LIGHT,'hair divisions')
    p.ribs([[(24.9+i*.77,21.7),(27.2+i*.58,24.5)] for i in range(4)]+
           [[(60.1,31),(61.7,30.5)],[(59.8,33.1),(61.1,32.8)]],
           .43,.101,.113,LIGHT,'outstretched hand and face')


def add_relief(face, center_x, center_z, side, distant):
    """Add one of the paired plates to the supplied recessed doorway facade."""
    if side not in ('left','right'):
        raise ValueError('side must be left or right')
    panel=Panel(face,center_x,center_z,side,distant)
    octagonal_border(panel)
    if side=='left':
        left_worker(panel)
    else:
        right_worker(panel)
