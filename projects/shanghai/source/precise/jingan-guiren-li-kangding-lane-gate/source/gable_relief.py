"""Relief on the public street face of Guiren Li, Kangding East Road.

Drawing coordinates are pixels on the rectified February 2020 street survey.
The two hanging panels were measured individually. Heights and X are shared
with the plaster frontage; d is the projection outward from its face.
"""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely import make_valid

DATA=Path(__file__).resolve().parents[1]/'measurements'
STONE='Gable | warm grey mineral render'
LIP='Gable | raised grey plaster edges'
SHADOW='Gable | sheltered moulded stone'
FACE='Lane name | ivory porcelain'
FRAME='Lane name | buff cement frame'
INK='Lane name | dark green black script'

def finish(rgb,roughness):
    rgb=np.asarray(rgb)/255
    return {'color':np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4).tolist(),
            'roughness':roughness,'metallic':0.0}
PALETTE={STONE:finish([145,140,127],.88),LIP:finish([152,147,134],.84),
         SHADOW:finish([130,126,115],.91),FACE:finish([226,225,214],.55),
         FRAME:finish([165,153,124],.84),INK:finish([53,57,48],.77)}

def homog(src,dst):
    rows=[]
    targets=[]
    for (x,y),(u,v) in zip(src,dst):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        targets.extend([u,v])
    values=np.linalg.lstsq(rows,targets,rcond=None)[0]
    return np.append(values,1.).reshape(3,3)

def xy(H,points):
    a=np.atleast_2d(points)
    p=np.column_stack([a,np.ones(len(a))])@H.T
    return p[:,:2]/p[:,2:3]

def add_gable_relief(b,lod=False):
    coarse=lod is True or lod=='lod'
    with (DATA/'carving-plane.json').open() as file: plan=json.load(file)
    H=np.asarray(plan['drawing_to_metric_xz'])
    with (DATA/'lane-inscription.json').open() as file: plaque=json.load(file)
    def prism(outer,depth,rear,mat,label,holes=()):
        p=make_valid(Polygon(xy(H,outer),[xy(H,h) for h in holes]))
        b.prism(p,rear,depth,lambda x,z,d:(x,-d,z),mat,label)
    def curve(name,points,widths,depth,lift,mat=STONE):
        # Elliptical closed section carried normal to a drawn centreline.
        path=xy(H,points); width=np.broadcast_to(widths,len(path))
        radii=[]
        for i,(u,v) in enumerate(points):
            radial=xy(H,[(u+width[i],v)])[0]-path[i]
            radii.append(np.linalg.norm(radial))
        tangent=np.gradient(path,axis=0);tangent/=np.linalg.norm(tangent,axis=1,keepdims=True)
        norm=tangent[:,::-1].copy();norm[:,0]*=-1
        verts=[]; faces=[]; n=6 if coarse else 10
        for mid,axis,r in zip(path,norm,radii):
            for k in range(n):
                t=2*math.pi*k/n
                x,z=mid+axis*r*math.cos(t)
                verts.append((x,-(depth+lift*math.sin(t)),z))
        for i in range(len(path)-1):
            for k in range(n):
                j=(k+1)%n
                faces.append((i*n+k,i*n+j,(i+1)*n+j,(i+1)*n+k))
        faces.extend((tuple(range(n-1,-1,-1)),tuple(range((len(path)-1)*n,len(path)*n))))
        v=np.asarray(verts);v=v-v.mean(axis=0)
        volume=sum(v[f[0]]@np.cross(v[f[j]],v[f[j+1]]) for f in faces for j in range(1,len(f)-1))
        b.add(verts,faces if volume>0 else [f[::-1] for f in faces],mat,name)
    def arc(name,centre,rx,rz,begin,end,width,depth,lift,mat=LIP):
        angles=np.linspace(math.radians(begin),math.radians(end),10 if coarse else 20)
        c=np.asarray(centre)
        pts=np.array([c+[rx*math.cos(a),rz*math.sin(a)] for a in angles])
        curve(name,pts,width,depth,lift,mat)
    def leaf(name,base,tip,width,depth,lift,mat=LIP):
        a=np.asarray(base);btip=np.asarray(tip);t=np.linspace(0.,1.,5 if coarse else 9)
        pts=a+t[:,None]*(btip-a)
        widths=.30+width*np.sin(np.pi*t)**.8*(1.15-.32*t)
        curve(name,pts,widths,depth,lift,mat)
    def oval(name,u,v,rx,ry,depth,mat):
        a=np.linspace(0,2*math.pi,20 if coarse else 44,endpoint=False)
        prism(np.column_stack([u+rx*np.cos(a),v+ry*np.sin(a)]),depth,-.001,mat,name)
    def bezier(name,p,width,depth,lift,mat):
        t=np.linspace(0,1,10 if coarse else 18)
        pts=(1-t[:,None])**3*p[0]+3*(1-t[:,None])**2*t[:,None]*p[1]+3*(1-t[:,None])*t[:,None]**2*p[2]+t[:,None]**3*p[3]
        curve(name,pts,width,depth,lift,mat)
        return pts
    def solid_section(rings, label, material, capped=True):
        """Connect equal point-count rings on the measured facade and orient the closed shell."""
        count=len(rings[0][0]);verts=[];faces=[]
        for planar,depth in rings:
            pts=xy(H,planar)
            verts.extend((x,-depth,z) for x,z in pts)
        for i in range(len(rings)-1):
            for j in range(count):
                k=(j+1)%count
                faces.append((i*count+j,i*count+k,(i+1)*count+k,(i+1)*count+j))
        if capped:
            faces.extend((tuple(range(count-1,-1,-1)),tuple(range((len(rings)-1)*count,len(rings)*count))))
        else:
            off=(len(rings)-1)*count
            faces.extend((off+j,off+(j+1)%count,(j+1)%count,j) for j in range(count))
        v=np.asarray(verts);v=v-v.mean(axis=0)
        volume=sum(v[f[0]]@np.cross(v[f[j]],v[f[j+1]]) for f in faces for j in range(1,len(f)-1))
        b.add(verts,faces if volume>0 else [f[::-1] for f in faces],material,label)
    # The mirror is a blank convex oval. Its lower leaves, separate crowning
    # lobes and paired upturned scrolls are visible from the winter stations.
    theta=np.linspace(0,2*math.pi,24 if coarse else 48,endpoint=False)
    oval_line=np.column_stack((24*np.cos(theta),37*np.sin(theta)))
    # Softly convex central face, with an unlettered top and shallow nested arris.
    solid_section([(np.array([324,134])+ratio*oval_line,d) for ratio,d in
                   [(1.,-.001),(1.,.035),(.86,.047),(.52,.055),(.13,.058)]],
                  'Mirror | oval plaster field',STONE)
    for sign,side in [(-1,'left'),(1,'right')]:
        def hand(u,v):return [324+sign*u,v]
        arc('Mirror | '+side+' rolled frame',(324,134),27,39,92 if sign<0 else -88,
            270 if sign<0 else 88,2.8,.047,.015)
        for j,(off,vtip,vbase) in enumerate([(5,169,151),(12,168,143),(19,164,137)]):
            leaf(f'Mirror | {side} lower fold {j+1}',hand(off, vbase),hand(off-2.6,vtip),2.25,.058,.012)
        curve('Mirror | '+side+' upper scroll',[hand(19,117),hand(26,109),hand(35,112),hand(38,126),hand(47,131),hand(57,123),hand(64,112)],[2,3.5,4,4,4.5,3,1.2],.041,.022)
        curve('Mirror | '+side+' lower scroll',[hand(2,171),hand(6,179),hand(13,181),hand(21,177),hand(22,171)],[2,3,3.4,2.7,1],.049,.019)
        leaf('Mirror | '+side+' upper inward leaf',hand(21,109),hand(3,92),5.6,.058,.023)
        leaf('Mirror | '+side+' crown side lobe',hand(17,103),hand(9,83),6.4,.052,.027)
    leaf('Mirror | crown middle lobe',(324,106),(324,76),7.1,.060,.031)
    # The tapered pendant immediately below the mirror is a separate carving.
    curve('Mirror | pendant stem',[(324,179),(325,193),(325,209),(326,227),(326,248),(326,262)],[2,4,4,3.5,3,1.1],.028,.017)
    for j,(v,rad) in enumerate([(196,8),(207,11),(216,10),(237,8),(248,9),(256,5)]):
        curve(f'Mirror | pendant collar {j+1}',[(325-rad,v-1),(320,v+2),(326,v+4),(331,v+2),(326+rad,v-1)],[1.3,2.2,2.3,2.2,1.3],.044,.016)
    # Distinct measured anchor points for each drop, including the differences
    # in level on the undeformed study drawing.
    for side,cx,v,tip in [('left',162.,209.,458.),('right',493.,194.,440.)]:
        offset=1 if side=='right' else -1
        oval(side+' | round festoon boss',cx,v,20.,18.,.023,STONE)
        arc(side+' | raised lower boss rim',(cx,v-1),23.,21.,0,177,3.0,.032,.017)
        arc(side+' | small inner boss lip',(cx,v-1),17.,15.,5,172,1.35,.032,.008)
        ribbon=[(cx,v+18),(cx,v+50),(cx+.5,v+73),(cx+1.,v+100),(cx+1.,v+119),(cx+1.5,v+156),(cx+2.,tip-23)]
        curve(side+' | thin suspension ribbon',ribbon,[2.1,2.2,2.7,2.,2.,1.6,1.25],.020,.011)
        for sg in [-1,1]:
            curve(f'{side} | folded upper ribbon {sg:+}',[(cx,v+74),(cx+sg*9,v+86),(cx+sg*15,v+90),(cx+sg*12,v+96),(cx+sg*3,v+108)],[1,1.4,1.9,1.9,.8],.030,.012)
        bend=v+144
        base=[(cx-29,bend-3),(cx-25,bend+4),(cx-11,bend+8),(cx+1,bend+9),(cx+14,bend+7),(cx+24,bend+3),(cx+30,bend-7)]
        curve(side+' | small transverse swag',base,[1.7,2.8,3.4,3.7,3.2,2.4,1.6],.031,.017)
        if not coarse:
            for k in range(9):
                t=k/8;xx=cx-24+48*t
                yy=bend+2+7*math.sin(t*math.pi)
                leaf(f'{side} | transverse swag cut {k+1}',(xx-1.5,yy-2),(xx+2,yy+3),1.15,.040,.009)
        for k in range(5):
            yy=tip-49+8*k
            arc(f'{side} | lower overlapping scale {k+1}',(cx+2,yy),8.5-(.4*k),5.7,7,172,1.8,.036+(.001*k),.012)
        leaf(side+' | pendant terminal',(cx+2,tip-15),(cx+1,tip-2),3.4,.030,.014)
        curve(side+' | terminal tie',[(cx-8,tip-1),(cx-3,tip-3),(cx+3,tip-2),(cx+8,tip-4)],[.8,1.6,1.5,.8],.033,.009)
        # Raised festoon silhouette and two interleaved rows of cut leaves.
        start=(293,154) if side=='left' else (355,151)
        end=(183,218) if side=='left' else (470,203)
        cp=np.asarray([start,(start[0]+offset*29,start[1]+50),(end[0]-offset*26,end[1]+10),end],float)
        bezier(side+' | festoon backing',cp,6.4,.032,.023,SHADOW)
        n=12 if coarse else 20
        for k,tv in enumerate(np.linspace(.04,.97,n)):
            p=(1-tv)**3*cp[0]+3*(1-tv)**2*tv*cp[1]+3*(1-tv)*tv**2*cp[2]+tv**3*cp[3]
            dp=3*(1-tv)**2*(cp[1]-cp[0])+6*(1-tv)*tv*(cp[2]-cp[1])+3*tv**2*(cp[3]-cp[2]);dp/=np.linalg.norm(dp)
            normal=np.array([-dp[1],dp[0]])
            for sg in [1,-1]:
                leaf(f'{side} | festoon leaf {k+1:02d} {sg:+}',p-dp*3.5,p+dp*3.5+sg*normal*(3.5+2.8*math.sin(tv*math.pi)+.8*math.sin(k)),1.7+.75*math.sin(tv*math.pi),.051,.014)
    to_drawing=homog(plaque['source_outer_frame'],plaque['drawing_outer_frame'])
    outer=np.asarray(plaque['source_outer_frame'],float)
    inset=np.asarray(plaque['face_in_source'],float)
    def remap(vertices):return xy(to_drawing,vertices)
    prism(remap(outer),.037,-.001,FRAME,'Name | cement back and squared outside lip')
    # A narrow projecting outer lip, chamfered reveal and inner fillet catch
    # the light separately in the 2021 close-up. The pale sign sits behind them.
    moulding=[(outer,.035),(outer,.057),(outer*.94+inset*.06,.070),
              (outer*.69+inset*.31,.069),(outer*.61+inset*.39,.060),
              (outer*.20+inset*.80,.054),(outer*.10+inset*.90,.058),
              (inset,.055),(inset,.035)]
    solid_section([(remap(loop),depth) for loop,depth in moulding],
                  'Name | stepped and chamfered cement surround',FRAME,False)
    prism(remap(inset),.045,.036,FACE,'Name | pale inset sign field')
    for let in plaque['letters']:
        for i,shape in enumerate(let['strokes']):
            prism(remap(shape['exterior']),.0485,.0448,INK,f"Name | {let['character']} stroke {i+1}",[remap(v)for v in shape['holes']])
