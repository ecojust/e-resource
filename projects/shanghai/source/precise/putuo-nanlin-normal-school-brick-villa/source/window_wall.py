"""The brick window wall in Fayhoo's April 2016 photograph of the Nanlin school."""
import json
from math import asin, cos, pi, sin
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from fabric import (DARK, FRAME, GLASS, GRAY, MORTAR, RED, RED_STONE, STONE,
                    chart, face, metric, paint)

SOURCE = Path(__file__).absolute().parent
READINGS = json.loads((SOURCE.parent/'measurements/window-wall-2016.json').read_text())
CORNICE = [(119,452),(234,451),(500,459),(700,465),(946,473),
           (1205,486),(1455,499),(1658,513),(1800,521),(2074,538)]
FACING = [f'Nanlin | radial red voussoir {i}' for i in range(4)]
PALETTE = {name:paint(rgb) for name,rgb in zip(FACING,[(147,77,56),(159,84,58),(139,70,51),(154,77,52)])}
LIGHT = 'Nanlin | reflected window glass'
PALETTE[LIGHT] = paint((93,108,108),.23,.22)


def lintel(u,v):
    """Interpolate the high edge of the dentil cornice at an image abscissa."""
    return float(np.interp(u,[p[0] for p in CORNICE],[p[1] for p in CORNICE]))+v


def band(points, upper_px, lower_px):
    return chart([(x,y+upper_px) for x,y in points]
                 + [(x,y+lower_px) for x,y in reversed(points)])


def arch_properties(row):
    l,r=row['jamb_x']
    mid=(l+r)/2
    sill=row['sill_y']
    x0,z0=metric(l,sill)
    if 'hidden_base_m' in row: z0=row['hidden_base_m']
    x1,_=metric(r,sill)
    spring=metric(mid,row['impost_y'])[1]
    top=metric(mid,row['intrados_crown_y'])[1]
    center=(x0+x1)/2
    half=(x1-x0)/2
    rise=top-spring
    if rise<.008:
        return center,half,z0,spring,0.,0.,0.
    radius=(half*half+rise*rise)/(2*rise)
    return center,half,z0,spring,radius,top-radius,asin(half/radius)


def arc(cx,cz,r,angles):
    return [(cx+r*sin(t),cz+r*cos(t)) for t in angles]


def outline(row,steps=28):
    c,h,base,spring,r,cz,theta=arch_properties(row)
    if not r:
        return box(c-h,base,c+h,spring)
    head=arc(c,cz,r,np.linspace(theta,-theta,steps+1))
    return Polygon([(c-h,base),(c+h,base),*head])


def arch_bricks(b,row,lod):
    c,h,base,spring,r,cz,theta=arch_properties(row)
    if not r:
        return
    name=row['id']
    thick=.27 if name.startswith('central') else .235
    if name=='left blind arch':thick=.30
    n=max(11,round(2*theta*r/.09))
    steps=32 if lod else 52
    def strip(r1,r2,t0,t1,s):
        tt=np.linspace(t0,t1,s+1)
        return Polygon(arc(c,cz,r1,tt)+arc(c,cz,r2,reversed(tt)))
    face(b,strip(r,r+thick,-theta,theta,steps),-.024,.021,MORTAR,name+' arch bedding')
    for i in range(n):
        a=-theta+2*theta*i/n+.0035/r
        d=-theta+2*theta*(i+1)/n-.0035/r
        face(b,strip(r+.003,r+thick-.009,a,d,2 if lod else 4),
             -.050-(.012 if i==n//2 else 0),-.022,FACING[i%4],name+' splayed arch bricks')
    # A narrow projecting hood turns horizontal for a short distance at each stop.
    hood=LineString(arc(c,cz,r+thick+.030,np.linspace(-theta,theta,steps+1)))
    e=hood.coords[0];end=hood.coords[-1]
    full=LineString([(e[0]-.10,e[1]),*hood.coords,(end[0]+.10,end[1])])
    face(b,full.buffer(.031,cap_style='flat',join_style='mitre'),-.105,-.018,RED_STONE,name+' hood mould')


def window_sash(b,row,hole,lod):
    name=row['id']
    rim=.055
    inner=hole.buffer(-rim,join_style='mitre')
    face(b,hole.difference(inner),.115,.200,FRAME,name+' rebated outer frame')
    lo,base,hi,top=inner.bounds
    mid=(lo+hi)/2
    transom=metric(sum(row['jamb_x'])/2,row['main_transom_y'])[1]
    bars=[box(lo-.03,transom-.033,hi+.03,transom+.033)]
    nx=row['vertical_lights'];ny=row['lower_rows']
    for k in range(1,nx):
        x=lo+(hi-lo)*k/nx
        half=.032 if nx%2==0 and k==nx//2 else .017
        bars.append(box(x-half,base-.01,x+half,top+.01))
    for k in range(1,ny):
        z=base+(transom-base)*k/ny
        bars.append(box(lo-.01,z-.018,hi+.01,z+.018))
    grille=inner.intersection(unary_union(bars))
    face(b,grille,.131,.194,FRAME,name+' transom and muntins')
    glass=inner.difference(grille)
    for j,poly in enumerate(sorted( getattr(glass,'geoms',[glass]),key=lambda p:(p.centroid.x,p.centroid.y) )):
        if poly.area>1e-7:
            face(b,poly,.187,.205,LIGHT if (j+len(name))%7==0 else GLASS,name+' individual panes')
    l,z,r,_=hole.bounds
    face(b,box(l-.10,z-.112,r+.10,z-.005),-.145,.083,STONE,name+' projecting sill')
    if name.startswith(('central','stepped')):
        apron(b,name,l,r,z,lod)


def apron(b,name,l,r,z,lod):
    c=(l+r)/2;w=r-l
    border=box(l+.012,z-.76,r-.012,z-.119)
    inner=box(c-w*.286,z-.635,c+w*.286,z-.269)
    face(b,border.difference(inner),-.065,.018,RED,name+' brick apron frame')
    face(b,inner,-.039,.010,RED_STONE,name+' terracotta relief ground')
    # The two small scrolls curl inward around a central leaf.
    a=(inner.bounds[2]-inner.bounds[0])*.47
    cy=z-.46
    for sign in [-1,1]:
        points=[(c+sign*.028,cy+.082),(c+sign*.19*a,cy+.112)]
        for t in np.linspace(.03,1,11 if lod else 21):
            angle=1.15+5.0*t
            radius=(1-.80*t)
            points.append((c+sign*a*(.52+.44*radius*cos(angle)),cy+.113*radius*sin(angle)))
        curve=LineString(points).buffer(.029,quad_segs=2,join_style='round')
        face(b,curve,-.096,-.037,STONE,name+' carved paired foliate scroll')
    face(b,Polygon([(c,cy-.136),(c-.054,cy-.028),(c,cy+.079),(c+.054,cy-.028)]),
         -.101,-.036,STONE,name+' carved centre leaf')


def lower_openings():
    # The central three and the entrance can be seen individually through or
    # above the garden planting. Sills behind the screen wall are approximate.
    rows=[]
    for name,l,r,top,shoulder,base in [
        ('lower west visible light',570,630,824,830,966),
        ('lower porch-side light',819,870,810,817,962),
        ('lower west hooded window',994,1078,823,833,954),
        ('lower east brick arch',1338,1414,826,836,945),
        ('ground pedimented entry',1616,1702,800,800,1017)]:
        rows.append(dict(id=name,jamb_x=[l,r],intrados_crown_y=top,impost_y=shoulder,
                         sill_y=base,main_transom_y=top+32,vertical_lights=3,lower_rows=2,
                         hidden_base_m=.09 if 'entry' in name else .91))
    return rows


def add_window_wall(b,lod=False):
    upper=READINGS['upper_openings'];lower=lower_openings()
    # Each carved opening is a true hole in the wall prism. The partial arch
    # at the left is filled in grey brick and stays distinct from the nine lights.
    all_rows=upper+lower
    openings=[outline(row,16 if lod else 28) for row in all_rows]
    top=[metric(u,v) for u,v in CORNICE]
    front=Polygon([(top[0][0],0),(top[-1][0],0),*reversed(top)])
    cut=unary_union(openings)
    face(b,front.difference(cut),0,.34,GRAY,'2016 window wall with recessed doors and windows')
    belt=READINGS['mid_red_belt_pixels']
    belt=[(119,606),*belt,(2074,667)]
    for off,thickness in [(-92,12),(-5,12),(62,6),(178,8)]:
        face(b,band(belt,off,off+thickness).intersection(front).difference(cut),
             -.008,.012,RED,'red facing brick stringcourse '+str(off))
    for row,hole in zip(all_rows,openings):
        window_sash(b,row,hole,lod)
        if row in upper or row['id']=='lower east brick arch':
            arch_bricks(b,row,lod)
    blind=dict(id='left blind arch',jamb_x=[164,282],intrados_crown_y=554,
               impost_y=603,sill_y=615)
    arch_bricks(b,blind,lod)
    # The taller right-hand return runs behind the scroll gable at its end.
    # At the left it turns inward above the terminal pier of the stone rail.
    short=chart([(119,452),(234,451),(234,415),(132,415),(119,407)])
    face(b,short,0,.35,GRAY,'south end lower parapet')
    left_cap=chart([(117,408),(135,414),(235,414),(235,407),(138,406),(117,400)])
    face(b,left_cap,-.065,.39,RED_STONE,'south end parapet cap')
    high=chart([(1447,497),(1658,513),(1763,517),(1763,419),
                (1453,392),(1447,409)])
    face(b,high,.205,.54,GRAY,'raised grey parapet behind north gable')
    coping=chart([(1445,406),(1453,390),(1764,416),(1764,423),
                  (1458,398),(1451,411)])
    face(b,coping,.137,.59,RED_STONE,'raised parapet coping and inward return')
    for a,d,depth,mat in [(0,5,-.14,RED_STONE),(5,12,-.09,RED),(13,21,-.055,RED),(23,29,-.11,RED_STONE)]:
        face(b,band(CORNICE,a,d),depth,.015,mat,'continuous corbelled eave mould')
    # Individual brick teeth cast the slots visible below the long upper ledge.
    for k,x in enumerate(np.linspace(128,2064,99)):
        d=5.5 if lod else 5.8
        bracket=chart([(x-d,lintel(x-d,11)),(x+d,lintel(x+d,11)),
                       (x+d-1,lintel(x+d,20)),(x-d+1,lintel(x-d,20))])
        face(b,bracket,-.138,-.049,FACING[(k+2)%4],'alternating cornice dentils')
    # The second cornice above the ground floor follows a discernible strip
    # through the planting and the raised pediment to the right.
    sillline=[(119,745),(430,748),(890,754),(1038,760),
              (1210,765),(1455,771),(1650,780),(1850,786),(2074,790)]
    for a,d,depth,mat in [(0,4,-.116,STONE),(4,13,-.085,RED),(13,18,-.058,RED_STONE)]:
        face(b,band(sillline,a,d).intersection(front).difference(cut),depth,.012,mat,'ground floor cornice')
    ped=chart([(1554,787),(1657,699),(1754,790)])
    inner=ped.buffer(-.125,join_style='mitre')
    face(b,ped.difference(inner),-.244,.018,RED_STONE,'ground entrance triangular moulded pediment')
    face(b,inner,-.123,.015,STONE,'ground entrance stone tympanum')
    # A narrow central cartouche and two curling sprays survive in the stone face.
    x,z=metric(1656,755)
    cart=Point(x,z).buffer(1.,quad_segs=10)
    from shapely.affinity import scale
    oval=scale(cart,.156,.225,origin=(x,z))
    face(b,oval.difference(oval.buffer(-.027)),-.174,-.123,STONE,'entrance oval cartouche')
    for sign in (-1,1):
        pts=[(x+sign*t*.59,z-.18+.112*sin(t*pi*2.5)-.045*t)for t in np.linspace(.08,1,15)]
        face(b,LineString(pts).buffer(.032,quad_segs=2),-.167,-.123,STONE,'entrance carved foliate spray')
