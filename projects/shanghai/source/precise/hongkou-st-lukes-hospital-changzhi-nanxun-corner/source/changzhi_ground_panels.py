"""Sealed rectangular ground-storey panels on Nanxun Road, visible in January 2021.

The district view published in 2023 controls the first supports and fascia.
The fourth to sixth drops are visible in both opposing 2021 exposures.
"""
from shapely.geometry import Polygon, box

# Distance from the end of the chamfer, in the common street frame.
SPANS = ((.59, 2.95), (3.47, 7.90), (8.52, 10.34), (10.95, 12.86), (13.47, 15.48))
FAR_DROPS = ((9.51, .32, .415), (11.94, .33, .365), (14.43, .34, .305))
# Depth of plaster returns is estimated from their visible shadow.
DEPTH = .068
BASE = .041

def inset_faces(layout):
    top = layout['low_fascia'] - .142
    return [box(left, BASE, right, top) for left, right in SPANS]

def add_sealed_panels(builder, face, layout, skin, finish, stone):
    for number, profile in enumerate(inset_faces(layout), 1):
        # Each closed back meets the solid main wall along its four reveal edges.
        skin(builder, face, profile, -.39, -DEPTH, finish,
             'sealed plaster in recess '+str(number))
    belt = layout['low_fascia']
    # The first three supports already belong to the registered entrance component.
    for number, (s, width, fall) in enumerate(FAR_DROPS, 4):
        half = width / 2
        shape = Polygon([(s-half, belt-.095), (s+half, belt-.095),
                         (s+.77*half, belt-fall), (s-.78*half, belt-fall)])
        skin(builder, face, shape, -DEPTH, .056, stone,
             'sealed fascia hanging block '+str(number))
