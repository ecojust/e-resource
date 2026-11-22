"""Street-facing dormer visible in Antigng's September 2015 photograph of No. 3 Shaoxing Road."""
from pathlib import Path
from math import cos, pi
from shapely.geometry import Polygon
from profile_tools import BRICK as TILE, cb, bricks_uv

GLASS = 'Muted blue glazing'
FRAME = 'Dark casement frame and muntins'
WALL = 'Grey dormer cheeks'
EDGE = 'Pale edge flashing'
GUTTER = 'Painted gutter and downpipe'
FELT = 'Shadow under tile laps'
PALETTE = {}
for name,rgb in [(TILE,(255,255,255)),(GLASS,(88,108,124)),(FRAME,(58,48,47)),(WALL,(138,136,128)),(EDGE,(173,173,153)),(GUTTER,(64,52,51)),(FELT,(72,51,46))]:
    PALETTE[name] = dict(color=[(v/255)**2.2 for v in rgb],roughness=.52 if name==GLASS else .86)
PALETTE[TILE]['texture']=str(Path(__file__).with_name('finish.png'))

def roof_y(t):
    return -.66+1.12*t

def roof_z(t):
    return .27+.38*t+1.94*t*t

def section(builder, x1,x2, points, depth, material, label):
    vertices=points+[(y,z-depth) for y,z in reversed(points)]
    builder.prism(Polygon(vertices),x1,x2,lambda y,z,x:(x,y,z),material,label=label)

def tile_band(builder, xa,xb,row,lod):
    lo=row/14
    hi=(row+1)/14
    width=.175 if not lod else .35
    # Each tile overlaps the next course at its lower edge. The rear edge is buried.
    x=xa-(width*.5 if row%2 else 0)
    while x<xb:
        left=max(x+.003,xa)
        right=min(x+width-.003,xb)
        if right-left>.012:
            front=max(0,lo-.022)
            pts=[(roof_y(front), roof_z(front)+.043), (roof_y((lo+hi)/2),roof_z((lo+hi)/2)+.029),(roof_y(hi),roof_z(hi)+.015)]
            section(builder,left,right,pts,.046,TILE,'Lapped reddish tile')
        x+=width

def model(b,lod=False):
    for xa,xb in [(-1.36,-.63),(.63,1.36),(-.63,.63)]:
        row_count=14 if xa!=-.63 else 5
        path=[(roof_y(k/14),roof_z(k/14)) for k in range(row_count+1)]
        section(b,xa,xb,path,.105,FELT,'Curved roof deck')
        for row in range(row_count):
            tile_band(b,xa,xb,row,lod)
    for side in (-1,1):
        x=side*1.366
        section(b,x-.028,x+.028,[(roof_y(k/14),roof_z(k/14)+.046) for k in range(15)],.115,EDGE,'Light curved edge of roof')
    # The dormer is open behind the sashes. Its jambs meet the steep upper roof.
    cheek=Polygon([(-.207,.70),(-.207,2.25),(.46,2.45),(.46,.90),(-.007,.71)])
    for x in (-.616,.616):
        b.prism(cheek,x-.029,x+.029,lambda y,z,xx:(xx,y,z),WALL,label='Side wall of dormer')
    cb(b,-.63,.63,-.211,-.12,.685,.85,WALL,'Apron below window')
    cb(b,-.63,.63,-.211,.13,2.03,2.245,WALL,'Head above twin casements')
    for x in (-.561,.561):
        cb(b,x-.052,x+.052,-.205,-.125,.84,2.04,WALL,'Grey outer jamb')
    cb(b,-.626,.626,-.263,-.123,.811,.865,FRAME,'Projecting sill')
    for x in (-.504,0,.504):
        cb(b,x-.024,x+.024,-.227,-.163,.852,2.057,FRAME,'Outside jamb or meeting stile')
    for x in (-.252,.252):
        cb(b,x-.24,x+.24,-.157,-.139,.882,2.021,GLASS,'Twin-light casement glass')
        cb(b,x-.012,x+.012,-.220,-.167,.867,2.028,FRAME,'Vertical glazing bar')
    for z in (.867,1.266,1.655,2.038):
        cb(b,-.517,.517,-.222,-.165,z-.016,z+.016,FRAME,'Continuous horizontal glazing bar')
    for y,z,dx in [(-.267,2.265,.684),(-.291,2.300,.672)]:
        section(b,-dx,dx,[(y,z),( .44,z+.205)],.039,GUTTER,'Shallow projecting cover over window')
    # The front lip is raised, leaving an open channel between it and the roof toe.
    cb(b,-1.394,1.394,-.755,-.672,.112,.163,GUTTER,'Bottom of street gutter')
    cb(b,-1.394,1.394,-.766,-.747,.112,.258,GUTTER,'Outer gutter lip')
    cb(b,-1.394,1.394,-.676,-.651,.112,.249,GUTTER,'Inner gutter lip')
    bricks_uv(b)
