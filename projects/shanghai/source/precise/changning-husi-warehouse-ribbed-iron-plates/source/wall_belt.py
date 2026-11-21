"""Measured appearance of the waist belt in a photograph of the Husi warehouse."""
from math import cos,sin,pi
from shapely.geometry import Polygon

def surface(rgb,roughness,metal=0.):
    def linear(channel):
        x=channel/255
        return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
    return {'color':[linear(x)for x in rgb],'roughness':roughness,'metallic':metal}
PALETTE={'grey brick':surface((134,135,129),.91),'cool brick':surface((122,125,121),.90),
         'umber brick':surface((187,134,90),.85),'dark red brick':surface((156,103,71),.87),
         'bedding mortar':surface((165,157,143),.95),'iron casting':surface((51,53,50),.83,.22),
         'iron ridge':surface((73,73,68),.73,.23),'iron pin':surface((84,80,72),.78,.28),
         'weathered cap':surface((140,139,128),.92)}
CENTRES=(-.125,.125)

def add_building(b,lod=False):
    def box(name,l,r,front,back,low,high,material):
        b.box(((l+r)/2,(front+back)/2,(low+high)/2),(r-l,back-front,high-low),material,label=name)
    def flat(name,poly,front,back,material):
        b.prism(Polygon(poly),-back,-front,lambda u,z,d:(u,-d,z),material,name)
    half=.83
    box('mortar bed',-half,half,.004,.135,0,1.01,'bedding mortar')
    for row in range(14):
        z=row*.072
        belt=6<=row<=9
        if lod: starts=[-half,-.415,0,.415,half] if row%2==0 else [-half,-.62,-.2,.20,.62,half]
        else: starts=[-half]+sorted(x for k in range(-7,8)if -half+.045<(x:=k*.236+(.118 if row%2 else 0))<half-.045)+[half]
        for j,(l,r)in enumerate(zip(starts,starts[1:])):
            mat=('dark red brick' if (row+2*j)%5==0 else 'umber brick') if belt else ('cool brick' if (row+j)%4==0 else 'grey brick')
            box('masonry course %02d'%(row+1),l+.0025,r-.0025,-.002,.005,z+.003,z+.069,mat)
    box('lower narrow orange sill',-half,half,-.041,-.001,.375,.396,'umber brick')
    for left,right in [(-half,-.251),(.251,half)]:
        n='left' if left<0 else 'right'
        box(n+' bottom orange course',left,right,-.029,.001,.429,.457,'dark red brick')
        box(n+' shallow orange course',left,right,-.055,.001,.457,.504,'umber brick')
        box(n+' orange projecting high brick',left,right,-.072,.001,.504,.561,'dark red brick')
        box(n+' widened orange projecting course',left,right,-.092,.001,.561,.603,'umber brick')
        box(n+' fascia below the coping',left,right,-.144,.001,.603,.678,'umber brick')
    box('continuous brick fascia',-half,half,-.14,.001,.678,.721,'umber brick')
    box('continuous thin grey cap',-half,half,-.176,.001,.721,.752,'weathered cap')
    for j,c in enumerate(CENTRES):
        tag=('left' if j==0 else 'right')
        box(tag+' backing plate',c-.121,c+.121,-.036,-.004,.396,.672,'iron casting')
        for k,(dx,dz) in enumerate([(-.116,-.122),(0,-.126),(.113,-.119),(.114,0),(.108,.119),(-.107,.12),(-.113,.005)]):
            # Each tapered rib rises to a spine. The recessed panels remain visible on both sides.
            vx=c+.004;vz=.528;t=(dx*dx+dz*dz)**.5;nx=-dz/t;nz=dx/t
            p0=(vx+dx*.14,vz+dz*.14);p1=(vx+dx,vz+dz)
            vs=[]
            for u,z,width,peak in [(p0[0],p0[1],.019,.082),(p1[0],p1[1],.008,.056)]:
                vs.extend([(u-nx*width,-.036,z-nz*width),(u,-peak,z),(u+nx*width,-.036,z+nz*width)])
            b.add(vs,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(0,3,5,2)],'iron ridge',tag+' rib %d'%(k+1))
        nn=6 if lod else 12
        profile=[(c+.031*cos(2*pi*k/nn),.528+.031*sin(2*pi*k/nn))for k in range(nn)]
        flat(tag+' raised round pin head',profile,-.093,-.067,'iron pin')
    # The entire original block remains in the city. This is the visible wall finish from the study image.
