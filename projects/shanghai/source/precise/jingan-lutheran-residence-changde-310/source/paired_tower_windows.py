"""Timber casements, fanlights and moulded red brick on the upper tower at Changde Road 310."""
import json
import math
from pathlib import Path

RECORD = Path(__file__).resolve().parents[1] / 'measurements' / 'paired-tower-windows.json'
BRICK='Tower windows | moulded red brick'
RECESS='Tower windows | shaded brick soffit'
LIP='Tower windows | raised brick lip'
KEY='Tower windows | projecting red keystone'
SILL='Tower windows | pale stone sill'
TIMBER='Tower windows | red-brown painted frame'
BEAD='Tower windows | glazing bar'
GLASS='Tower windows | muted green reflection'
LIGHT='Tower windows | pale window reflection'
FAN='Tower windows | ochre fanlight reflection'

def finish(rgb, rough, metal=0.):
    cs=[s/255. for s in rgb]
    return dict(color=[s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4 for s in cs],roughness=rough,metallic=metal)

PALETTE={BRICK:finish((157,81,57),.91),RECESS:finish((92,57,47),.93),LIP:finish((174,96,65),.83),
         KEY:finish((160,83,57),.88),SILL:finish((179,170,151),.78),TIMBER:finish((111,53,40),.57),
         BEAD:finish((127,67,47),.58),GLASS:finish((90,103,91),.28,.12),
         LIGHT:finish((128,135,119),.24,.15),FAN:finish((152,139,106),.33,.12)}

def openings():
    return json.loads(RECORD.read_text())['windows']

def _box(b,l,r,y0,y1,z0,z1,mat,name):
    b.box(((l+r)/2,(y0+y1)/2,(z0+z1)/2),(r-l,y1-y0,z1-z0),mat,label=name)

def _extrude(b,poly,front,back,mat,name):
    area=sum(x*z2-x2*z for (x,z),(x2,z2) in zip(poly,poly[1:]+poly[:1]))
    if area<0:poly=list(reversed(poly))
    n=len(poly)
    vertices=[(x,y,z) for y in (front,back) for x,z in poly]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend((i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n))
    b.add(vertices,faces,mat,name)

def _ribbon(b,x,z,rx,rz,sx,sz,a,t,front,back,mat,name,n):
    angles=[a+(t-a)*i/n for i in range(n+1)]
    def vertex(ax,az,v):return x+ax*math.cos(v),z+az*math.sin(v)
    # One closed extrusion with quad annular end faces; no triangle spans the clear arch.
    p=[vertex(rx,rz,v) for v in angles];q=[vertex(sx,sz,v) for v in angles]
    k=len(p);verts=[(px,y,pz) for y in (front,back) for row in (p,q) for px,pz in row];faces=[]
    for i in range(n):
        j=i+1
        faces.extend([(i,k+i,k+j,j),(2*k+j,3*k+j,3*k+i,2*k+i),(j,2*k+j,2*k+i,i),(k+i,3*k+i,3*k+j,k+j)])
    faces.extend([(0,2*k,k*3,k),(n,k+n,3*k+n,2*k+n)])
    b.add(verts,faces,mat,name)

def add_tower_windows(b,lod=False):
    far=lod is True or lod in ('lod','low','distant','far')
    for index,row in enumerate(openings()):
        key=row['key'];l,r=row['left'],row['right'];x=(l+r)/2;rad=(r-l)/2
        z0=row['bottom'];zc=row['spring'];rise=row['top']-zc;front=row['front_y_m']
        wood=row['frame_y_m'];glass=row['glass_y_m'];rx=row['outer_radius_x'];rz=row['outer_crown_z']-zc
        segments=22 if far else 48
        def bx(a,d,y0,y1,low,high,mat,label):
            _box(b,a,d,y0,y1,low,high,mat,key+' | '+label)
        def ring(inner_x,inner_z,outer_x,outer_z,a,t,y0,y1,mat,label,count=segments):
            _ribbon(b,x,zc,inner_x,inner_z,outer_x,outer_z,a,t,y0,y1,mat,key+' | '+label,count)
        # The brick archivolt has a rolled inner edge and two ridges on its outer face.
        ring(rad,rise,rx,rz,0,math.pi,-.065,front+.05,BRICK,'continuous brick arch')
        ring(rad,rise,rad+.055,rise+.055,0,math.pi,-.116,-.055,LIP,'inner arch moulding')
        ring(rx-.095,rz-.105,rx-.062,rz-.065,0,math.pi,-.101,-.057,LIP,'outer arch moulding')
        ring(rx-.196,rz-.228,rx-.161,rz-.177,0,math.pi,-.093,-.061,BRICK,'intermediate roll')
        ring(rad,rise,rad+.033,rise+.036,0,math.pi,front-.015,wood+.073,RECESS,'intrados visible behind projecting arch')
        ring(rad+.1,rise+.105,rx+.019,rz+.060,math.pi*.462,math.pi*.538,-.155,-.061,KEY,'keystone',4 if far else 7)
        for side in (-1,1):
            j=x+side*(rad+(rx-rad)/2)
            # The two arches share the central impost. Each half stops at its visible bearing.
            iw=min(rx-rad+.016,.326)
            bx(j-iw/2,j+iw/2,-.093,.032,zc-.056,zc+.038,LIP,'impost at spring '+str(side))
            poly=[(j-iw*.37,zc-.055),(j+iw*.37,zc-.055),(j+iw*.22,zc-.118),(j,zc-.155),(j-iw*.24,zc-.115)]
            _extrude(b,poly,-.074,.022,BRICK,key+' | drop below impost '+str(side))
        bx(l-.073,r+.073,-.094,wood+.084,z0-.119,z0+.008,SILL,'projecting stone sill and return')
        for a,d,side in ((l-.024,l+.007,'left'),(r-.007,r+.024,'right')):
            bx(a,d,-.001,wood+.08,z0+.003,zc,RECESS,side+' shaded jamb return')
        for a,d,k in ((l,l+.052,'left'),(r-.052,r,'right')):
            bx(a,d,wood,wood+.071,z0,zc,TIMBER,k+' vertical stile')
        bx(l,r,wood-.005,wood+.076,z0,z0+.056,TIMBER,'bottom rail')
        # The fanlight is glazed up to the actual curve. Its shadow follows the front intrados.
        rb=rad-.041;rzb=rise-.044
        ring(rb,rzb,rad,rise,0,math.pi,wood,wood+.069,TIMBER,'curved fanlight frame')
        poly=[(x+rb*math.cos(v*math.pi/segments),zc+rzb*math.sin(v*math.pi/segments))for v in range(segments+1)]
        _extrude(b,poly,glass,glass+.012,FAN,key+' | arched fanlight glass')
        fbase=row['fan_base_z'];bx(l,r,wood-.008,wood+.069,fbase-.045,fbase+.046,TIMBER,'rail below fanlight')
        bx(l+.052,r-.052,glass,glass+.012,fbase+.046,zc,FAN,'fanlight lower glazing')
        # Two radial-head uprights and a horizontal meeting bar are visible through the shade.
        for col in (-1,1):
            dx=col*rb*.335;lim=zc+rzb*math.sqrt(1-(dx/rb)**2)
            bx(x+dx-.012,x+dx+.012,wood+.020,wood+.055,fbase+.034,lim,BEAD,'short fanlight upright '+str(col))
        chord=zc+.26*rzb;dx=rb*math.sqrt(1-.26**2)
        bx(x-dx,x+dx,wood+.020,wood+.055,chord-.011,chord+.011,BEAD,'upper fanlight crossbar')
        bx(x-.027,x+.027,wood-.012,wood+.076,z0+.041,fbase-.037,TIMBER,'central meeting stile')
        rails=row['timber_transoms_z'];strong=rails[0] if row['tier']=='middle' else None
        for i,v in enumerate(rails):
            h=.041 if v==strong else .017
            bx(l+.023,r-.023,wood-(.009 if v==strong else -.014),wood+.063,v-h,v+h,TIMBER if v==strong else BEAD,'transom '+str(i+1))
        cuts=sorted([z0+.047,fbase-.040,*rails])
        for j,(a,d) in enumerate(((l+.043,x-.019),(x+.019,r-.043))):
            for i,(bottom,top) in enumerate(zip(cuts,cuts[1:])):
                color=LIGHT if (i+j+index)%3==0 else GLASS
                bx(a,d,glass,glass+.012,bottom,top,color,'rectangle light '+str(j+1)+'.'+str(i+1))
                if not far and top-bottom>.09:
                    bx(a,a+.009,glass-.012,glass+.003,bottom+.014,top-.014,BEAD,'putty fillet '+str(j+1)+'.'+str(i+1))
