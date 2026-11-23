"""The visible return and the unornamented support below the surveyed upper storey."""
from shapely.geometry import box
from photo_architecture import Facade
from street_finishes import GREEN, LOWER, UPPER, BASE
from street_wall import RIGHT, UPPER_LEFT, LEFT, REAR_Y, SILL, IRON

def add_returns(b, lod=False):
    # Plain cut planes close the building where the street cameras lose sight
    # of it. The high storey's return ends at the same working section Y=8.11.
    main_back_y = 4.43
    high_back_y = 8.11
    wing_end_x = 11.38
    wing_back_y = 5.12
    right = Facade(b,(RIGHT,0),(RIGHT,main_back_y),'central house court return')
    right.wall(0,.245,thickness=.17,material=BASE)
    right.wall(.245,2.81,thickness=.17,material=LOWER)
    right.wall(2.81,5.43,thickness=.17,material=UPPER)
    left = Facade(b,(UPPER_LEFT,main_back_y),(UPPER_LEFT,0),'central house left section')
    left.wall(2.81,5.29,thickness=.16,material=UPPER)
    # The eaves climb along the front; the top of its supporting wall follows
    # the same rise instead of leaving a line of sky beneath the high end.
    front = Facade(b,(-1,0),(1,0),'upper wall/eaves seat')
    from shapely.geometry import Polygon
    front.prism(Polygon([(UPPER_LEFT,5.23),(RIGHT,5.23),(RIGHT,5.47),(UPPER_LEFT,5.28)]),-.222,0,UPPER,'under fascia')
    b.box(((LEFT+UPPER_LEFT)/2,.36,2.86),(UPPER_LEFT-LEFT,.72,.09),SILL,label='low street wall/visible coping return')
    b.box((LEFT+.07,.36,1.42),(.14,.72,2.84),LOWER,label='low street wall/east cut')
    b.box(((UPPER_LEFT+RIGHT)/2,.15,.075),(RIGHT-UPPER_LEFT,.30,.15),BASE,label='street foundation/wall joint')
    b.box((11.30,(REAR_Y+wing_back_y)/2,2.80),(.16,wing_back_y-REAR_Y,5.60),UPPER,label='recessed wing/west section')
    b.box(((RIGHT+wing_end_x)/2,wing_back_y-.08,2.80),(wing_end_x-RIGHT,.16,5.60),UPPER,label='recessed wing/rear section')
    # Only the seen upper storey's outline is carried back as a plain cut solid.
    # The photographs do not determine rooms, interior openings, or the rest of the parcel.
    b.box((2.61,(main_back_y+high_back_y)/2,2.59),(5.78,high_back_y-main_back_y,5.18),UPPER,label='high house/undecorated lower support at rear cut')
    b.box(((UPPER_LEFT+RIGHT)/2,main_back_y-.09,2.62),(RIGHT-UPPER_LEFT,.18,5.24),UPPER,label='central house/rear cut')
    b.plan_prism(box(UPPER_LEFT,0,RIGHT,main_back_y),5.15,5.24,UPPER,'central house/closed eaves bed')
    b.plan_prism(box(RIGHT,REAR_Y,wing_end_x,wing_back_y),5.52,5.60,UPPER,'recessed wing/closed eaves bed')
    # The close photograph shows three dark-green upright service sleeves at
    # the roughcast/painted wall junction. Their feet meet a common pale plinth.
    b.box((4.12,-.043,.176),(.31,.23,.352),SILL,label='street corner/services plinth')
    for i,x in enumerate((4.015,4.115,4.215)):
        b.tube([(x+.014,-.061,.346),(x-.024,-.069,2.82)],.041,GREEN,8 if lod else 12,'street corner/green service sleeve '+str(i+1))
    b.box((4.12,-.036,2.819),(.286,.11,.045),IRON,label='street corner/services wall fixing')

def fit_walls_to_roof_decks(builder):
    """Close the two solid external wall heads against the actual underside triangles."""
    import numpy as np
    from shapely.geometry import Polygon
    # Walls sit a millimetre inside the face below, keeping the plaster seam clear.
    plans = {
        'central projecting roof': (box(UPPER_LEFT+.001, .001, RIGHT-.001, 4.429), 5.16),
        'setback wing roof': (box(4.101, REAR_Y+.001, 11.379, 5.119), 5.525),
    }
    for part in list(builder.parts):
        if 'boarded underside' not in part['label']:
            continue
        group = next((key for key in plans if key in part['label']), None)
        if group is None:
            continue
        footprint, bottom = plans[group]
        vertices = np.asarray(part['vertices'])
        for indices in part['triangles']:
            a, c, d = vertices[list(indices)]
            normal = np.cross(c-a,d-a)
            if normal[2] >= -1e-6:
                continue
            overlap = Polygon((a[:2],c[:2],d[:2])).intersection(footprint)
            if overlap.is_empty or overlap.area < 1e-7:
                continue
            from shapely.geometry.polygon import orient
            outline = list(orient(overlap,sign=1).exterior.coords)[:-1]
            # The board plane is intersected vertically, not through its normal.
            # Three millimetres of overlap keep the construction seam sealed.
            top = [(x,y,a[2] - (normal[0]*(x-a[0]) + normal[1]*(y-a[1])) / normal[2] + .003)
                   for x,y in outline]
            if min(p[2] for p in top) <= bottom:
                raise ValueError((group,'roof seat descends below its wall head'))
            n = len(outline)
            faces = [tuple(reversed(range(n))),tuple(range(n,n*2))]
            faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
            builder.add([(x,y,bottom)for x,y in outline]+top,faces,UPPER,group+' / plaster wall meets roof underside')
