"""The four-storey street face, central glazed stair and entrance at 42 Wanping Road."""
import json
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from street_materials import RED, YELLOW, STEEL, GLASS, CREAM, LIME, GREEN, STONE, SHADE, RED_DOOR
from stair_ornament import draped_panel, frieze
from portal_sculpture import add_portal
from four_window_bays import bay_openings

# Read from a rectified 2019 photograph at 50 px per metre in the 22 m study frame.
def rect_px(x0,y0,x1,y1):
    return box(x0/50-12.2,16.75-y1/50,x1/50-12.2,16.75-y0/50)
LEFT,RIGHT=-11.46,11.35
CENTRE=(-1.68,1.57)
TOP=13.73
COLOUR_CHANGE=6.15
LIGHTS={
 'upper left flat':((59,204,117,308),2,4),
 'lower left flat':((57,369,115,466),2,4),
 'first floor 1':((56,550,110,643),2,4),'first floor 2':((154,546,183,641),1,4),
 'first floor 3':((204,546,255,642),2,4),'first floor 4':((280,543,308,644),1,4),
 'first floor 5':((363,546,389,643),1,4),'first floor 6':((414,543,456,643),2,4),
 'first floor 7':((476,545,503,642),1,4),'first floor 8':((715,542,745,642),1,4),
 'first floor 9':((772,541,807,643),2,4),'first floor 10':((836,541,856,643),1,4),
 'first floor 11':((972,541,997,642),1,4),'first floor 12':((1017,541,1057,643),2,4),
 'first floor 13':((1090,539,1112,642),1,4),
 'lower left grille':((153,713,232,777),3,3),'lower middle grille':((329,713,402,777),3,3),
 'lower middle grille 2':((430,712,504,778),3,3),'lower north grille':((736,712,811,778),3,3),
 'shop window 1':((949,717,1017,772),2,2),'shop window 2':((1102,715,1168,772),2,2),
}
DOORS={'southern entry':(45,711,82,833),'central entry':(582,726,642,837),
       'service door':(896,715,948,836), 'second service door':(1064,715,1102,836)}
PAIRS=[(123,189),(262,355),(429,529),(606,641)]
CENTRE_X=[(572,596),(610,637)]

def glazework(face,hole,cols,rows,name,grille,lod):
    x0,z0,x1,z1=hole.bounds
    lip=hole.buffer(-.035,join_style=2)
    face.solid(hole,-.14,-.125,SHADE,name+' | reveal')
    face.solid(hole.difference(lip),-.113,-.056,STEEL,name+' | sash')
    face.solid(lip,-.118,-.106,GLASS,name+' | glazing')
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols
        face.rect(x-.014,x+.014,z0+.035,z1-.035,-.105,-.060,STEEL,name+' | mullions')
    for j in range(1,rows):
        z=z0+(z1-z0)*j/rows
        face.rect(x0+.034,x1-.034,z-.013,z+.013,-.106,-.063,STEEL,name+' | rails')
    face.rect(x0-.016,x1+.016,z0-.042,z0+.004,-.068,.033,STONE,name+' | sill')
    if grille:
        for i in range(1,8):
            x=x0+(x1-x0)*i/8
            face.rail([(x,-.025,z0+.025),(x,-.025,z1-.025)],.011,STEEL,name+' | grille',5 if lod else 8)

def add_street(face,lod=False):
    normal={name:(rect_px(*pixels),c,r) for name,(pixels,c,r) in LIGHTS.items()}
    for row,(y0,y1) in enumerate(PAIRS):
        for column,(x0,x1) in enumerate(CENTRE_X):
            normal[f'stair lights {row+1}.{column+1}']=(rect_px(x0,y0,x1,y1),1,3 if row in (1,2) else 1)
    doors={name:rect_px(*bounds) for name,bounds in DOORS.items()}
    voids=unary_union([h for h,c,r in normal.values()]+list(doors.values()))
    low=box(LEFT,0,RIGHT,COLOUR_CHANGE).difference(voids)
    centre=box(CENTRE[0],COLOUR_CHANGE,CENTRE[1],15.36)
    reds=box(LEFT,COLOUR_CHANGE,RIGHT,TOP).difference(centre)
    face.solid(low,-.25,0,YELLOW,'lower storeys | yellow brick')
    face.solid(centre.difference(voids),-.25,0,YELLOW,'staircase | continuous yellow brick pier')
    face.solid(reds.difference(unary_union([voids,*[box(*b) for b in bay_openings()]])),-.25,0,RED,'upper storeys | red brick')
    face.solid(box(LEFT,.0,RIGHT,.28).difference(voids),-.009,.023,STONE,'street wall | base course')
    for name,(h,c,r) in normal.items():glazework(face,h,c,r,name,'grille' in name,lod)
    for name,h in doors.items():
        x0,z0,x1,z1=h.bounds
        face.solid(h,-.16,-.147,SHADE,name+' | entrance recess')
        face.solid(h.buffer(-.026,join_style=2),-.146,-.096,GREEN if 'entry' in name else RED_DOOR,name+' | flush door')
        if name=='central entry':
            for x in (x0-.155,x1+.016):
                face.rect(x,x+.145,0,z1+.15,-.017,.14,LIME,'central entry | pale jamb')
            face.rect(x0-.16,x1+.17,z1,z1+.34,-.018,.15,CREAM,'central entry | incised lintel')
        else:
            face.rect(x0-.033,x1+.033,z1,z1+.06,-.040,.055,STONE,name+' | lintel')
    evidence=Path(__file__).resolve().parents[1]/'measurements/central-cast-panels.json'
    sampled={(v['side'],v['edge']):v['rectified_y'] for v in json.loads(evidence.read_text())['readings']}
    for side,(x0,x1) in [('left',(571,600)),('right',(608,638))]:
        for level in ('upper','middle','lower'):
            y0=sampled.get((side,level+' panel head'),sampled['left',level+' panel head'])
            y1=sampled[side,level+' panel foot']
            draped_panel(face,rect_px(x0,y0,x1,y1).bounds,lod)
    # Broad crown to both sides of the top stair windows.
    for x0,x1 in [(526,571),(639,688)]:
        draped_panel(face,rect_px(x0,105,x1,151).bounds,lod)
    # The horizontal cast stringcourse stops either side of the stepped entrance head.
    z=16.75-674/50
    for x0,x1 in [(LEFT,-1.40),(1.33,RIGHT)]:frieze(face,x0,x1,z,lod)
    for x0,x1,lo,hi,projection in [(-1.40,1.33,2.31,3.38,.13),(-1.14,1.11,3.34,3.72,.17),(-.96,.78,3.67,3.92,.14)]:
        face.rect(x0,x1,lo,hi,-.018,projection,CREAM,'central entry | stepped head')
    add_portal(face,doors['central entry'],lod)
