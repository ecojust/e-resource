"""Reconstruction of the paired steel entrance leaves, 1040 North Suzhou Road.

The four horizontally framed panels on each leaf and their stepped open web are
traced from the before/after conservation photographs. The construction depth
and scale are estimates. X runs across the door, Y inward, Z upward.
"""
from math import cos,pi,sin
def finish(rgb,roughness,metallic):
    def linear(v):
        s=v/255.
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=roughness,metallic=metallic)
PALETTE={
    'blackened leaf frame':finish((57,60,59),.65,.28),
    'graphite web':finish((72,75,74),.65,.24),
    'plate face':finish((69,72,72),.66,.35),
    'rolled panel edge':finish((97,99,94),.55,.27),
    'pressed panel bevel':finish((81,85,82),.59,.28),
    'dark interlock':finish((49,51,49),.73,.19),
    'stone threshold':finish((150,145,131),.89,0),
    'edge fastening':finish((88,87,83),.56,.27)
}
def box(b,name,x1,x2,y1,y2,z1,z2,material):
    v=[(x,y,z)for z in(z1,z2)for y in(y1,y2)for x in(x1,x2)]
    faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    b.add(v,faces,material,name)
def ring(b,label,cx,cz,width,height,sections,material):
    def contour(w,h,y):
        return [(cx-w,y,cz-h),(cx+w,y,cz-h),(cx+w,y,cz+h),(cx-w,y,cz+h)]
    rows=[contour(width/2-a,height/2-a,y) for a,y in sections];v=sum(rows,[])
    faces=[]
    for j in range(len(rows)-1):
        for i in range(4):
            a=j*4+i;d=j*4+(i+1)%4
            faces.append((a,d,d+4,a+4))
    b.add(v,faces,material,label)
def bolt(b,label,x,y,z,lod):
    n=5 if lod else 12;r=.0085
    v=[(x+r*cos(2*pi*i/n),y+.0025,z+r*sin(2*pi*i/n))for i in range(n)]
    v += [(x+r*cos(2*pi*i/n),y-.0009,z+r*sin(2*pi*i/n))for i in range(n)]
    v.append((x,y-.004,z))
    f=[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
    f.extend((i+n,(i+1)%n+n,2*n)for i in range(n))
    b.add(v,f,'edge fastening',label)
CENTRES=(.294,.824,1.354,1.884)
def add_building(b,lod=False):
    box(b,'sloping stone sill',-1.145,1.145,-.104,.19,0,.07,'stone threshold')
    for side,cx in [('left',-.505),('right',.505)]:
        # Both leaves have narrow exterior stiles and a wider central meeting stile.
        for sign in (-1,1):
            inner=(sign==1)==(side=='left')
            x=cx+sign*.448;half=.048 if inner else .036
            box(b,side+' '+('meeting'if inner else'outer')+' stile',x-half,x+half,-.017,.055,.083,2.16,'blackened leaf frame')
        for z in (.105,2.135):
            box(b,side+' main crossrail '+str(z),cx-.471,cx+.471,-.018,.053,z-.026,z+.026,'blackened leaf frame')
        for ix,z in enumerate(CENTRES):
            label=side+' pressed tablet '+str(ix+1)
            box(b,label,cx-.337,cx+.337,-.035,.026,z-.100,z+.100,'plate face')
            outer=(0,-.008);shoulder=(.008,-.042);bead=(.015,-.047)
            inside=(.022,-.039);seat=(.030,-.033)
            ring(b,label+' folded rim',cx,z,.728,.240,[outer,shoulder,bead,inside,seat]if not lod else[outer,bead,seat],'rolled panel edge')
            ring(b,label+' sloped reveal',cx,z,.690,.210,[(0,-.036),(.013,-.029)],'pressed panel bevel')
            for sign in (-1,1):
                x=cx+sign*.347
                box(b,label+' side return '+str(sign),x-.017,x+.017,-.008,.031,z-.13,z+.13,'graphite web')
            # Two narrow floating bars are visible between each adjacent pair of tablets.
            if ix<3:
                for k,d in enumerate((.213,.305)):
                    box(b,label+' crossweb '+str(k),cx-.451,cx+.451,-.004,.035,z+d-.018,z+d+.018,'graphite web')
                for sign in (-1,1):
                    x=cx+sign*.182
                    box(b,label+' short middle upright '+str(sign),x-.018,x+.018,-.004,.035,z+.12,z+.412,'graphite web')
                    x=cx+sign*.347
                    for k,(lo,hi) in enumerate(((.12,.213),(.305,.410))):
                        box(b,label+' step '+str(sign)+' '+str(k),x-.017,x+.017,-.003,.033,z+lo,z+hi,'graphite web')
            for sign in (-1,1):
                for v in (-1,1):
                    bolt(b,label+' fastening',cx+sign*.313,-.035,z+v*.075,lod)
        for x in (cx-.18,cx+.18):
            for center in (.150,2.060):
                box(b,side+' apron cleat',x-.017,x+.017,-.003,.031,center-.053,center+.053,'graphite web')
    box(b,'recessed meeting strip',-.011,.011,.043,.066,.084,2.158,'dark interlock')
