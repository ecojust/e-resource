"""Garden-door metalwork measured on the archived 1280 by 1919 portrait."""
import numpy as np
from shapely.geometry import Polygon, LineString


# Control points are in a twice-enlarged detail whose native origin is (503, 789).
# Each segment has two handles and a terminal point. Hidden centres under the
# later red paper are omitted. The opposite ends were read separately.
LOBES = [
    [(76,302),(72,316),(51,320),(43,304),(34,291),(34,244),(47,224),(55,211),(67,207),(76,220)],
    [(77,219),(67,206),(69,175),(80,160),(92,145),(108,146),(118,164)],
    [(118,164),(114,153),(109,137),(121,121),(132,109),(141,105),(149,115)],
    [(149,115),(141,99),(156,78),(183,67),(202,59),(233,50),(246,66)],
    [(247,66),(243,54),(255,34),(270,31),(288,25),(340,25),(354,36),(363,43),(368,52),(370,67)],
    [(371,67),(376,48),(398,48),(428,60),(451,68),(467,86),(473,105)],
    [(474,105),(481,91),(495,98),(510,109),(531,123),(548,158),(548,185),(547,194),(543,204),(539,215)],
    [(541,217),(555,206),(572,215),(579,230),(587,249),(586,288),(578,303),(572,315),(560,316),(555,304)]
]
RETURNS = [
    [(30,236),(37,215),(45,193),(52,198),(63,198),(70,210),(76,220)],
    [(76,174),(85,154),(97,145),(117,148)],
    [(132,107),(143,99),(148,97),(151,110)],
    [(231,40),(244,38),(247,44),(246,66)],
    [(375,62),(375,40),(390,38),(402,40)],
    [(462,72),(474,76),(482,89),(474,105)],
    [(542,216),(554,198),(564,191),(572,193)],
]
# Only the unmasked ends of these lightly visible bars are traced.
RAYS = [
    [(92,306),(135,310),(184,313),(240,316)],
    [(131,284),(159,289),(198,301),(240,310)],
    [(236,320),(236,313),(240,305),(245,296)],
    [(382,319),(381,308),(378,298),(373,291)],
    [(388,308),(438,290),(481,279),(506,276)],
    [(391,315),(440,314),(492,309),(540,307)],
]


def fit_fanlight(builder, lod, point, plate, wall, iron, pale, paper):
    def from_detail(pair, depth):
        u, v = pair
        return point((503 + u / 2) * 537 / 1280, (789 + v / 2) * 805 / 1919, depth)

    def cable(handles, radius, label):
        curve = [np.asarray(handles[0], dtype=float)]
        for index in range(1, len(handles), 3):
            a = curve[-1]
            b, c, d = np.asarray(handles[index:index+3], dtype=float)
            for t in np.linspace(0, 1, 4 if lod else 8)[1:]:
                curve.append((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d)
        axis = [from_detail(p, wall+.018)[[0,2]] for p in curve]
        # A flat wrought strip has a stable front plane at bends and returns.
        profile = LineString(axis).buffer(radius, quad_segs=2 if lod else 4)
        plate(builder,profile,wall+.013,wall+.033,iron,label)

    for loops, radius, prefix in [(LOBES,.0065,'scalloped outer grille'),(RETURNS,.004,'return'),(RAYS,.0045,'visible radial bar')]:
        for i, handles in enumerate(loops, 1):
            cable(handles, radius, f'fanlight/{prefix} {i}')

    diamond = Polygon([from_detail(p,wall+.004)[[0,2]] for p in [(194,211),(313,92),(431,207),(317,327)]])
    plate(builder, diamond,wall+.004,wall+.009,pale,'fanlight/paper gilt border in portrait')
    plate(builder, diamond.buffer(-.010,join_style='mitre'),wall,wall+.005,paper,
          'fanlight/red New Year paper in portrait')
