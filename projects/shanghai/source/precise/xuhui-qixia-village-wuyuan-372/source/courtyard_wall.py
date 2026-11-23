"""Yellow court walls, specific grey gates and observed address plates in the courtyard lane."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import LineString,box
from shapely.ops import unary_union
from court_masonry import Camera,slab,layer,FENCE,PIER,DOOR,SIGN,INK,STEEL,TRIM,PIPE
COURT=-2.40
def xi(c,p):return c.wall(p,COURT)[0]
def gate(b,cam,obs,number,lod):
    l,r,a,c,lt,rt,p0,p1=obs
    xs=[xi(cam,p) for p in (l,r,a,c)]
    zleft,zright=[cam.wall(q,COURT)[2]for q in (lt,rt)]
    for i,(lo,hi,z) in enumerate([(xs[0],xs[1],zleft),(xs[2],xs[3],zright)]):
        slab(b,lo,hi,COURT,COURT+.24,0,z-.07,PIER,f'No {number} | gate pier {i+1}')
        slab(b,lo-.025,hi+.025,COURT-.027,COURT+.265,z-.082,z,TRIM,f'No {number} | pier cap {i+1}')
    slab(b,xs[1],xs[2],COURT+.11,COURT+.14,.015,min(zleft,zright)-.12,DOOR,f'No {number} | dark inward gate')
    a=cam.wall(p0,COURT-.029);c=cam.wall(p1,COURT-.029)
    x0,x1=sorted((a[0],c[0]));z0,z1=sorted((a[2],c[2]));h=z1-z0;w=x1-x0
    slab(b,x0,x1,COURT-.046,COURT-.015,z0,z1,SIGN,f'No {number} | enamel plaque')
    # The actual photographs show a single large numeral. The tiny Chinese line is illegible at this scale.
    coords=([(0.71,.86),(.40,.88),(.27,.72),(.26,.46),(.37,.25),(.61,.24),(.74,.39),(.73,.52),(.57,.60),(.36,.54),(.26,.43)]
            if number==6 else [(.21,.86),(.77,.86),(.47,.22)])
    line=LineString([(x0+w*u,z0+h*v)for u,v in coords]).buffer(max(.004,w*.047),cap_style=1,join_style=1)
    layer(b,line,COURT-.052,.009,INK,f'No {number} | raised numeral')
    return xs[0],xs[-1],(zleft+zright)/2

def add_boundary(b,ends,lod):
    c6,c7,c9=Camera(17),Camera(18),Camera(20)
    g6=gate(b,c6,[(113,395),(146,395),(186,393),(211,392),(117,390),(204,388),(192,410),(204,427)],6,lod)
    g7=gate(b,c7,[(81,391),(103,391),(195,389),(230,389),(86,384),(223,378),(92,416),(103,433)],7,lod)
    from no9_court import controls
    end9=max(xi(c9,p)for p in controls()['foreground']['right_pier_crown'])
    begin9=min(xi(c9,p)for p in controls()['foreground']['left_pier_crown'])
    for left,right,lo,hi,label in [(ends['left'],begin9-.86,1.66,1.67,'south end'),
                                    (end9+.72,g7[0],1.74,g7[2]-.14,'middle garden bays'),
                                    (g7[1],g6[0],g7[2]-.12,g6[2]-.14,'between Nos 7 and 6'),
                                    (g6[1],ends['right'],g6[2]-.14,g6[2]-.14,'No 6 front')]:
        if right<=left:continue
        poly=box(left,0,right,1).exterior.coords
        from shapely.geometry import Polygon
        field=Polygon([(left,0),(right,0),(right,hi),(left,lo)])
        layer(b,field,COURT+.025,.18,FENCE,'Gardens | '+label)
        band=Polygon([(left,lo-.045),(right,hi-.045),(right,hi+.015),(left,lo+.015)])
        layer(b,band,COURT+.003,.237,TRIM,'Gardens | coping at '+label)
    for lo,hi in [(begin9-.86,begin9),(end9,end9+.72)]:
        slab(b,lo,hi,COURT+.10,COURT+.14,.02,1.65,DOOR,'Gardens | dark side of No 9 gate')
    # Light timber pickets above the identifiable No 6 eastern wall.
    left,right=g6[1]+.14,ends['right']-.13
    top=g6[2]-.12
    if right>left:
        pitch=.13 if not lod else .17
        for x in np.arange(left,right,pitch):
            slab(b,x,x+.061,COURT+.12,COURT+.157,top,top+.37,FENCE,'No 6 garden | vertical fence slat')
        slab(b,left,right+.045,COURT+.155,COURT+.18,top+.12,top+.15,PIER,'No 6 garden | connecting batten')
