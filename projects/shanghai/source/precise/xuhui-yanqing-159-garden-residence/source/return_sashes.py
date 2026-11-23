"""Photographed opening steel casements on the right return of 159 Yanqing Road."""
import json
from math import cos, radians, sin
from pathlib import Path

from shapely.geometry import box

from upper_sash import GREEN, GREEN_GLASS, LIGHT, LIGHT_GLASS, RECESS

HERE=Path(__file__).resolve().parent
MEASURE=json.loads((HERE.parent/'measurements/return-casement-photo-control.json').read_text())
OPENINGS=MEASURE['reference_openings']
GROUPS={'near-open':['near-open'],'attic-green':['attic-green-first','attic-green-second'],
        'attic-pale':['attic-pale']}


def casement_grid(face,width,bottom,top,columns,levels,paint,glass,label):
    height=top-bottom
    frame=min(.021,.055*width)
    frame_side=box(0,bottom,width,top)
    clear=box(frame,bottom+frame,width-frame,top-frame)
    face.solid(frame_side.difference(clear),-.016,.012,paint,label+' | folded steel perimeter')
    xs=[frame]+[width*j/columns for j in range(1,columns)]+[width-frame]
    zs=[bottom+frame]+[bottom+height*h for h in levels]+[top-frame]
    bar=min(.014,.037*width)
    for x in xs[1:-1]:
        face.rect(x-bar/2,x+bar/2,zs[0],zs[-1],-.010,.010,paint,label+' | glazing upright')
    for z in zs[1:-1]:
        face.rect(xs[0],xs[-1],z-bar/2,z+bar/2,-.009,.011,paint,label+' | transom')
    for i,(a,b) in enumerate(zip(xs,xs[1:])):
        for j,(lo,hi) in enumerate(zip(zs,zs[1:])):
            left=a+(bar/2 if i else 0);right=b-(bar/2 if i<len(xs)-2 else 0)
            low=lo+(bar/2 if j else 0);high=hi-(bar/2 if j<len(zs)-2 else 0)
            face.rect(left,right,low,high,-.009,-.004,glass,label+' | individual glazed light')


def add_return_sash(f,name,bounds,lod=False):
    """Fit a return sash to (u0,z0,u1,z1), with positive local depth inside the building."""
    a,low,b,top=bounds;oa,ol,ob,ot=OPENINGS[name]
    w,h=b-a,top-low;sx,sz=w/(ob-oa),h/(ot-ol)
    paint=LIGHT if name=='attic-pale' else GREEN
    glass=LIGHT_GLASS if name=='attic-pale' else GREEN_GLASS
    label='return window | '+name
    opening=box(a,low,b,top);inner=opening.buffer(-min(.031,.06*w),join_style=2)
    f.solid(opening.difference(inner),-.068,-.018,paint,label+' | recessed fixed jamb')
    # Offset the shadow backing from the moving leaf to retain its real opening.
    # Continue the reveal to the rear board so an oblique street view cannot
    # see sky through the depth between the exterior wall core and the frame.
    lining=opening.buffer(.015,join_style=2).difference(inner)
    f.solid(lining,-.302,-.067,RECESS,label+' | side and head lining')
    f.solid(opening,-.306,-.294,RECESS,label+' | interior opening')
    if name=='near-open':
        axis=f.face(a+.695*w,.085,1,0)
        casement_grid(axis,w*.265,low+.055*h,top-.08*h,1,(.34,.66),paint,glass,
                      label+' | darker inner light beside open leaf')
    for key in GROUPS[name]:
        fit=MEASURE['leaves'][key];hinge=a+(fit['working_hinge_u']-oa)*sx
        bottom=low+(fit['sill']-ol)*sz;head=low+(fit['head']-ol)*sz
        width=fit['leaf_width_m']*sx;angle=radians(fit['swing_degrees'])
        plane=f.face(hinge,-.010*sx,cos(angle),-sin(angle))
        columns=3 if name=='near-open' else 1
        levels=[v['fraction_above_sill'] for v in fit['visible_transoms']]
        casement_grid(plane,width,bottom,head,columns,levels,paint,glass,'return open leaf | '+key)
        for z in (bottom+.18*(head-bottom),bottom+.83*(head-bottom)):
            f.rail([(hinge,-.010*sx,z-.023),(hinge,-.010*sx,z+.023)],
                   min(.012,.041*width),paint,'return open leaf | '+key+' | hinge barrel',6 if lod else 10)
