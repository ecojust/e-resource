"""Continuous brickwork, the two courses of arched windows and the ground openings."""
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from frontage_coordinates import facade_point, WINDOW_PLANES
from material_names import PLASTER,RED,WHITE,TEXTURES
from upper_windows import DATA, opening_profiles

def finish(rgb,rough=.88,metal=0.):
    f=np.asarray(rgb)/255.
    return dict(color=np.where(f<.04045,f/12.92,((f+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)

BUFF='Changchun terrace | pale sill stone'
CREAM='Changchun terrace | rendered spandrel panels'
WOOD='Changchun terrace | oxblood timber'
CLEAR='Changchun terrace | shaded ground glass'
IRON='Changchun terrace | iron drainpipes'
CORNICE='Changchun terrace | brown eave boards'
COURT='Changchun terrace | visible grey paving'
TERRA=['Changchun terrace | arch brick '+v for v in ('umber','orange','rose','russet','ochre')]
PALETTE={**{k:dict(texture=str(p),color=[1.,1.,1.],roughness=.93,metallic=0.)for k,p in TEXTURES.items()},
         BUFF:finish([166,148,122]),CREAM:finish([192,182,167]),WOOD:finish([91,63,52]),
         CLEAR:finish([68,72,68],.61),IRON:finish([75,74,69],.73,.17),CORNICE:finish([100,82,71]),COURT:finish([155,151,137])}
for k,rgb in zip(TERRA,[(155,92,67),(172,103,74),(170,96,75),(151,84,68),(161,100,78)]):PALETTE[k]=finish(rgb)
def photo(u,v,y=0.):
    x,_,z=facade_point(u,v,y)
    return(x,z)
def section(b,shape,y0,y1,mat,label):
    if shape.is_empty:return
    shape=set_precision(shape,1.e-7).simplify(3.e-7,preserve_topology=True)
    if shape.geom_type=='Polygon' and shape.area>1.e-7:
        b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)
    elif hasattr(shape,'geoms'):
        for part in shape.geoms:section(b,part,y0,y1,mat,label)
def block(b,l,r,f,k,lo,hi,mat,label):
    b.box(((l+r)/2,(f+k)/2,(lo+hi)/2),(r-l,k-f,hi-lo),mat,label=label)
def polygon_on_photo(points,y):
    return Polygon([photo(*q,y) for q in points])
def ring_point(row,t,rise):
    l,r,v=row['spring'];c,top=row['crown']
    x=c+(r-c if cos(t)>=0 else c-l)*cos(t)
    return (x+rise*cos(t),v-(v-top+rise)*sin(t))
def arch_course(b,row,y,tag,lod):
    # The pointed brick outer edge is distinct from the round or shallow glazing below.
    c,top=row['crown'];l,r,v=row['spring'];k=row['bay']
    shallow=row['row']=='upper' and k in range(3,7)
    width=8.2 if shallow else 13.2
    n=17 if shallow else 23
    full_curve=np.linspace(0,pi,49)
    ring=polygon_on_photo([ring_point(row,t,0)for t in full_curve]+[ring_point(row,t,width)for t in full_curve[::-1]],y)
    section(b,ring,y-.035,y+.015,RED,tag+' | brick arch bed')
    for i in range(n):
        t0=(i+.035)*pi/n;t1=(i+.965)*pi/n
        seg=np.linspace(t0,t1,3 if not lod else 2)
        shape=polygon_on_photo([ring_point(row,t,.2)for t in seg]+[ring_point(row,t,width-.2)for t in seg[::-1]],y)
        section(b,shape,y-.058-(.009 if i%4==1 else 0),y-.028,TERRA[(i*3+k)%len(TERRA)],tag+' | radiating facing bricks')
    # A hood with two straight upper shoulders dies into the brick at either side.
    if shallow:
        outer=[(l-8,v+.6),(l-7,v-4),(c-(c-l)*.61,top-4.8),(c,top-9.7),
               (c+(r-c)*.61,top-4.9),(r+7,v-4),(r+8,v+.6)]
    else:
        outer=[(l-13,v+.6),(l-12,v-8),(l-6.2,top-2.0),(c-(c-l)*.66,top-9.2),
               (c-2.1,top-16.0),(c,top-17.5),(c+2.8,top-16.4),
               (c+(r-c)*.66,top-9.1),(r+6.6,top-2.6),(r+12,v-8),(r+13,v+.6)]
    path=LineString([photo(*q,y)for q in outer])
    section(b,path.buffer(.076,cap_style=2,join_style=2),y-.173,y-.044,TERRA[3],tag+' | projecting outer hood')
    line=LineString([photo(u,v-.72,y)for u,v in outer])
    section(b,line.buffer(.043,cap_style=2,join_style=2),y-.190,y-.165,TERRA[4],tag+' | bevel along raised hood')
    if not shallow:
        for npos in [.22,.5,.78]:
            a=npos*pi;delta=.050 if npos!=.5 else .060
            shape=polygon_on_photo([ring_point(row,a-delta,1.1),ring_point(row,a+delta,1.1),ring_point(row,a+delta,14.6),ring_point(row,a-delta,14.6)],y)
            section(b,shape,y-.148,y-.048,TERRA[3],tag+' | moulded arch blocks')
    sill_left,sill_right,sill_v=row['sill']
    sill=polygon_on_photo([(sill_left-1.1,sill_v-.2),(sill_right+1.2,sill_v-.2),(sill_right+1.3,sill_v+1.6),(sill_left-1,sill_v+1.6)],y)
    section(b,sill,y-.088,y+.01,BUFF,tag+' | sill')
    # Pale rectangular spandrels terminate at the red belt above the floor below.
    foot=266 if row['row']=='upper' else 396
    t0=photo(sill_left+.55,sill_v+1.8,y);t1=photo(sill_right-.55,sill_v+1.8,y)
    z0=photo(c,foot,y)[1]
    if z0<min(t0[1],t1[1]):
        section(b,Polygon([t0,t1,(t1[0],z0),(t0[0],z0)]),y-.043,y-.010,CREAM,tag+' | light recessed spandrel')

# Visible lower-level openings. Four arched timber windows occupy the central bays;
# the left and right pairs have square lintels, including the rear building door.
GROUND_CENTRES=[70,188,307,394,490,586,695,808]
def ground_opening(k,y):
    ix=GROUND_CENTRES[k-1];w=29 if k in (1,2,7,8)else 27
    lower=-4.48
    if k in (1,2,7,8):
        tx,tz=photo(ix,427 if k in (1,2)else 425,y)
        half=abs(photo(ix+w,426,y)[0]-tx)
        return box(tx-half,lower,tx+half,tz)
    head=[photo(ix+w*cos(t),440-19*sin(t),y) for t in np.linspace(0,pi,37)]
    return Polygon([(head[-1][0],lower),(head[0][0],lower),*head])
def ground_frame(b,s,k,y,lod):
    tag='Ground opening '+str(k)
    l,base,r,zt=s.bounds
    section(b,s,y+.195,y+.235,CLEAR,tag+' | shaded infill')
    section(b,s.difference(s.buffer(-.055,join_style=2)),y+.055,y+.16,WOOD,tag+' | outer timber frame')
    cuts=[(l+(r-l)*f,.018)for f in (.25,.5,.75)]
    for x,half in cuts:
        section(b,s.intersection(box(x-half,base,x+half,zt)),y+.11,y+.175,WOOD,tag+' | glazing bars')
    for z in (base+(zt-base)*.45,zt-.65):
        section(b,s.intersection(box(l,z-.025,r,z+.025)),y+.095,y+.163,WOOD,tag+' | transom')
    if k in (1,2,7,8):
        for i in range(27 if not lod else 16):
            n=27 if not lod else 16
            xa=l+(r-l)*i/n;xb=l+(r-l)*(i+1)/n
            spread=(xa-(l+r)/2)*.035
            shape=Polygon([(xa+.004,zt+.006),(xb-.004,zt+.006),(xb-.004+spread,zt+.24),(xa+.004+spread,zt+.24)])
            section(b,shape,y-.058,y+.013,TERRA[(i+k)%5],tag+' | gauged flat arch')
        for x in (l-.09,r+.09):
            block(b,x-.14,x+.14,y-.19,y+.04,zt-.12,zt+.045,RED,tag+' | pier capital')
            block(b,x-.10,x+.10,y-.105,y+.04,base,zt-.12,RED,tag+' | entrance pier')
    else:
        outer=s.buffer(.14,join_style=2).difference(s)
        section(b,outer.intersection(box(l-.18,zt-.77,r+.18,zt+.21)),y-.068,y+.016,RED,tag+' | round brick head')
def limits():
    return photo(57,160,0)[0],photo(842,161,0)[0]
def add_front(b,lod=False):
    profiles=opening_profiles()
    left,right=limits()
    # The ends stop beyond the two paired attic bays. Only the photographed street elevation is retained.
    floor=-4.48;cap=photo(446,155,0)[1]
    boundaries=[left,photo(275,162,0)[0],photo(615,162,0)[0],right]
    zones=[(1,2,-.03),(3,6,0.),(7,8,-.03)]
    for side,(ka,kb,y) in enumerate(zones):
        l,r=boundaries[side:side+2];tag=['East paired bays','Central four bays','West paired bays'][side]
        cut=unary_union([profiles[f'{level}-{k:02}']for k in range(ka,kb+1)for level in ('lower','upper')]+[ground_opening(k,y)for k in range(ka,kb+1)])
        body=box(l,floor,r,cap).difference(cut)
        section(b,body,y,.38,PLASTER,tag+' | grey brick wall through all levels')
        if side==1:
            fill=box(l,photo(445,400,0)[1],r,cap).difference(cut)
            section(b,fill,y-.016,y+.001,RED,tag+' | red upper facing')
        else:
            for v0,v1 in [(156,204)]:
                z0=photo(446,v1,y)[1];z1=photo(446,v0,y)[1]
                section(b,box(l,z0,r,z1).difference(cut),y-.017,y+.001,RED,tag+' | red spandrel head')
            for k in range(ka,kb+1):
                for level,to in [('upper',299),('lower',420)]:
                    row=DATA[f'{level}-{k:02}'];a,c,v=row['sill']
                    top=photo((a+c)/2,v+1,y)[1];low=photo((a+c)/2,to,y)[1]
                    slab=box(photo(a+.2,v,y)[0],low,photo(c-.2,v,y)[0],top).difference(cut)
                    section(b,slab,y-.023,y+.001,RED,tag+' | brick beneath window')
        for v0,v1,projection,material,name in [(150.5,155,.113,CORNICE,'overhanging eave'),(155,157.8,.09,RED,'upper fillet'),(158,160,.068,RED,'upper bed'),(263.5,266,.104,BUFF,'upper floor sill band'),(267.2,270,.068,RED,'upper floor brick belt'),(393.0,397,.091,BUFF,'ground cornice'),(397.5,402,.13,RED,'ground fillet')]:
            z0=photo(446,v1,y)[1];z1=photo(446,v0,y)[1]
            stripe=box(l-.018,z0,r+.018,z1)
            if side!=1 and 263<v0<272:
                # At the paired bays this course stops at the spandrels; the grey piers continue past it.
                span=[]
                for k in range(ka,kb+1):
                    a,c,v=DATA[f'upper-{k:02}']['sill']
                    span.append(box(photo(a-.45,v,y)[0],z0-.1,photo(c+.45,v,y)[0],z1+.1))
                stripe=stripe.intersection(unary_union(span))
            section(b,stripe.difference(cut),y-projection,y+.014,material,tag+' | '+name)
        for k in range(ka,kb+1):
            for level in ['lower','upper']:
                row=DATA[f'{level}-{k:02}'];arch_course(b,row,y,level+' bay '+str(k),lod)
            ground_frame(b,ground_opening(k,y),k,y,lod)
    # The mortar lines and pipes have distinct convergences in this oblique survey.
    # Recover the shafts from each recorded image trace on the chosen local plane.
    from frontage_fittings import add_fittings
    add_fittings(b,lod)
