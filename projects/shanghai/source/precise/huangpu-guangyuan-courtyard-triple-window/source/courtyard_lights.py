"""Courtyard window bay in the photograph of Guangyuan Fang published with Lou Chenghao's article.

Three vertical lights sit in the same brown wooden frame. Beneath them the
photograph shows stepped horizontal mouldings and a shallow central cartouche.
"""
from math import sin,cos,pi

def paint(rgb,metal=0):
    v=[a/255. for a in rgb];return dict(color=[a/12.92 if a<=.04045 else ((a+.055)/1.055)**2.4 for a in v],roughness=.60 if metal else .82,metallic=metal)
PALETTE={m:paint(v) for m,v in [
    ('sand render',(179,153,127)),('buff render return',(156,135,114)),('joint shade',(127,112,99)),
    ('stone fascia',(167,145,118)),('lit stone fillet',(188,167,140)),('shadowed bed moulding',(144,125,105)),
    ('terracotta brown frame',(95,58,43)),('weathered wooden stiles',(112,69,52)),('dark lower sash',(85,52,43)),
    ('casement interior',(47,43,40)),('shaded glazing',(52,51,48)),('glass in shade',(62,61,58)),
    ('warm glass',(72,62,51)),('raised oval rim',(174,150,124)),('oval recess',(155,132,112))]}

def section(b,name,x0,x1,profile,m):
    n=len(profile);v=[(x,y,z) for x in (x0,x1)for y,z in profile]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,n+(i+1)%n,n+i)for i in range(n));b.add(v,faces,m,name)
def solid(b,name,x0,x1,y0,y1,z0,z1,m):
    section(b,name,x0,x1,[(y0,z0),(y1,z0),(y1,z1),(y0,z1)],m)
def add_building(b,lod=False):
    x0,x1=-1.13,1.13;lo,hi=-.86,.86;bottom,top=.87,2.08
    # The elevation has horizontal joints beside the window and a broad blank spandrel.
    solid(b,'back of upper wall',x0,x1,0,.21,top,2.32,'sand render')
    solid(b,'wall behind the apron',x0,x1,.0,.21,0,bottom,'sand render')
    for side,(left,right)in enumerate([(x0,lo),(hi,x1)]):
        solid(b,'side bed '+str(side),left,right,-.007,.21,bottom,top,'joint shade')
        for i in range(7):
            z=bottom+i*(top-bottom)/7
            solid(b,f'courses beside window {side}-{i}',left,right,-.020,.0,z+.004,z+(top-bottom)/7-.004,'sand render')
    for i,z in enumerate([.12,.45,2.207]):
        section(b,'horizontal stone band '+str(i),x0,x1,[(-.055,z),(.006,z),(.006,z+.031),(-.071,z+.031),(-.071,z+.014)],'stone fascia')
    section(b,'shaped window head',lo-.045,hi+.045,[(-.044,top),(.015,top),(.015,top+.066),(-.073,top+.066),(-.073,top+.048),(-.050,top+.031)],'lit stone fillet')
    solid(b,'outer frame side left',lo,lo+.060,.028,.140,bottom,top,'terracotta brown frame')
    solid(b,'outer frame side right',hi-.060,hi,.028,.140,bottom,top,'terracotta brown frame')
    solid(b,'outer frame head',lo,hi,.027,.145,top-.054,top,'terracotta brown frame')
    solid(b,'outer frame lower rail',lo,hi,-.005,.141,bottom,bottom+.062,'dark lower sash')
    inside=hi-lo-.12;step=inside/3
    for i in range(3):
        x=lo+.06+i*step;right=x+step
        if i>0:solid(b,'substantial timber mullion '+str(i),x-.035,x+.035,.014,.130,bottom+.018,top-.017,'weathered wooden stiles')
        left=x+(.036 if i else .003);r=right-(.036 if i<2 else .003)
        for a in [left,r-.019]:solid(b,f'casement stile {i}-{a:.3f}',a,a+.019,.064,.117,bottom+.052,top-.048,'dark lower sash')
        for z in [bottom+.06,top-.079]:solid(b,f'casement rail {i}-{z:.3f}',left,r,.062,.119,z,z+.023,'dark lower sash')
        solid(b,'reflecting glass '+str(i),left+.014,r-.014,.132,.144,bottom+.077,top-.071,['warm glass','shaded glazing','glass in shade'][i])
        if not lod:
            for a in [left+.016,r-.026]:solid(b,f'putty fillet {i}-{a:.3f}',a,a+.009,.086,.116,bottom+.08,top-.072,'terracotta brown frame')
    # The photograph resolves the shape of the oval, but no inscription.
    solid(b,'panel recessed ground',lo+.018,hi-.018,-.043,.006,.528,.775,'buff render return')
    for a in [lo+.020,hi-.054]:solid(b,'apron frame end '+str(a),a,a+.034,-.058,-.036,.519,.785,'stone fascia')
    for j,(z,depth)in enumerate([(.484,-.066),(.508,-.075),(.766,-.061)]):
        solid(b,'apron surround '+str(j),lo-.024,hi+.024,depth,.003,z,z+.023,'stone fascia')
    zz=.648;rx=.145;rz=.074;N=24 if lod else 48
    verts=[(rx*fac*cos(i*2*pi/N),d,zz+rz*fac*sin(i*2*pi/N))for fac,d in [(1.,-.046),(.88,-.066),(.73,-.060)]for i in range(N)]
    faces=[(k*N+i,k*N+(i+1)%N,(k+1)*N+(i+1)%N,(k+1)*N+i)for k in range(2)for i in range(N)]
    b.add(verts,faces,'raised oval rim','central oval return')
    panel=[(rx*.74*cos(i*2*pi/N),-.057,zz+rz*.74*sin(i*2*pi/N))for i in range(N)];b.add(panel,[tuple(range(N))],'oval recess','plain centre within the oval')
    for z,y,m in [(.795,-.074,'shadowed bed moulding'),(.825,-.103,'lit stone fillet')]:
        section(b,'sill along three lights '+str(z),lo-.057,hi+.057,[(y+.016,z),(.040,z),(.04,z+.038),(y,z+.027)],m)
