"""Photographed ochre brick frontage, canted casements and sill brackets at No.13."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from court_frontage import BRICK,finish

HERE=Path(__file__).resolve().parent
MEASURE=HERE.parent/'measurements'
SURVEY=json.loads((MEASURE/'no13-residential-facade.json').read_bytes())
PLACE=json.loads((MEASURE/'terrace-placement.json').read_bytes())
GREY='No13 | grey window surround'
EDGE='No13 | grey drip edge'
WOOD='No13 | dark brown window frames'
SHADOW='No13 | shaded reveal'
COVER='No13 | grey roofing'
GLASS=['No13 | sky reflection','No13 | warm reflected glass','No13 | shaded glass']
PALETTE={k:finish(rgb,r,m) for k,rgb,r,m in [
    (GREY,(142,139,132),.84,0),(EDGE,(94,92,90),.79,.05),(WOOD,(65,47,42),.62,.07),
    (SHADOW,(49,44,42),.90,0),(COVER,(117,109,98),.87,0),
    (GLASS[0],(128,146,154),.29,.14),(GLASS[1],(118,111,106),.34,.14),(GLASS[2],(86,93,94),.35,.14)]}
PALETTE[BRICK]=dict(texture=str(HERE/'guanghua-ochre-brick.png'),color=[1.,1.,1.],roughness=.92)

class Face:
    """Local width, height and inward depth of one facade."""
    def __init__(self,b,start,end,tag):
        self.b=b
        self.a=np.array(start,float)
        vector=np.array(end,float)-self.a
        self.width=np.linalg.norm(vector)
        self.axis=vector/self.width
        self.normal=np.array([-self.axis[1],self.axis[0]])
        self.tag=tag
    def point(self,x,z,depth):
        xy=self.a+x*self.axis+depth*self.normal
        return xy[0],xy[1],z
    def skin(self,shape,front,back,mat,name):
        self.b.prism(orient(shape,sign=1.),-back,-front,lambda x,z,d:self.point(x,z,-d),mat,self.tag+' | '+name)
    def bar(self,left,right,bottom,top,front,back,mat,name):
        if right>left and top>bottom:self.skin(box(left,bottom,right,top),front,back,mat,name)

def casement(face,x,width,low,high,depth,index,lod,opening=0.):
    direction=face.axis*math.cos(opening)-face.normal*math.sin(opening)
    # Hinged at the left in the frontal 2018 view.
    origin=face.a+x*face.axis+depth*face.normal
    leaf=Face(face.b,origin,origin+width*direction,face.tag)
    edge=.034
    shell=box(0,low,width,high).difference(box(edge,low+edge,width-edge,high-edge))
    leaf.skin(shell,-.017,.030,WOOD,'casement stile and rails')
    rows=4
    pitch=(high-low-2*edge)/rows
    for j in range(rows):
        z=low+edge+j*pitch
        leaf.bar(edge,width-edge,z,z+pitch,.004,.013,GLASS[(index+2*j)%len(GLASS)],'daylight glass')
        if j:
            leaf.bar(edge,width-edge,z-.014,z+.014,-.014,.018,WOOD,'horizontal glazing bar')
        if not lod:
            leaf.bar(edge,edge+.009,z,z+pitch,-.008,.008,WOOD,'glass edge bead')
            leaf.bar(width-edge-.009,width-edge,z,z+pitch,-.008,.008,WOOD,'glass edge bead')

def window(w,row,lod):
    l,r,b,t=[row[k]for k in ('trim_left','trim_right','trim_bottom','trim_top')]
    il,ir,iz,it=l+.083,r-.083,b+.066,t-.088
    frame=row['frame_recess_m'];void=box(il,iz,ir,it)
    ring=box(l,b,r,t).difference(void)
    w.skin(ring,-.032,.025,GREY,'rendered window casing')
    # Both camera directions show a slender edge along all three sides of the grey incised surround.
    bead=box(l+.019,b+.014,r-.019,t-.018).difference(box(l+.033,b+.03,r-.033,t-.032))
    w.skin(bead,-.041,-.026,EDGE,'casing edge bead')
    wall_lining=box(il-.016,iz-.016,ir+.016,it+.016).difference(void)
    w.skin(wall_lining,-.016,frame+.035,GREY,'window reveal')
    sill=Polygon([(il-.12,b+.055),(ir+.12,b+.055),(ir+.12,b-.057),(il-.12,b-.057)])
    w.skin(sill,-.129,.105,GREY,'projecting stone sill')
    w.bar(l+.04,r-.04,b-.196,b-.055,-.078,.012,GREY,'shallow recessed apron')
    for x in [l+.071,r-.196]:w.bar(x,x+.125,b-.325,b-.053,-.064,.012,GREY,'sill corbel')
    f=.037
    w.skin(void.difference(box(il+f,iz+f,ir-f,it-f)),frame-.04,frame+.019,WOOD,'fixed timber frame')
    bar=row['upper_transom_z']
    w.bar(il,ir,bar-.031,bar+.031,frame-.040,frame+.018,WOOD,'transom bar')
    leaves=row['columns']
    inner_l,inner_r=il+f,ir-f
    cuts=[inner_l+(inner_r-inner_l)*i/leaves for i in range(leaves+1)]
    trans_cuts=[inner_l,inner_r] if leaves==2 else [inner_l,cuts[1],cuts[3],inner_r]
    for k,(a,c) in enumerate(zip(trans_cuts,trans_cuts[1:])):
        w.bar(a,c,bar+.032,it-f,frame-.002,frame+.012,GLASS[(k+1)%3],'transom glass')
        if k:w.bar(a-.021,a+.021,bar+.029,it,frame-.037,frame+.014,WOOD,'transom muntin')
    for k,(a,c) in enumerate(zip(cuts,cuts[1:])):
        tilted=(row['label']=='Front bay face' and k==0)
        casement(w,a,c-a,iz+f,bar-.031,frame-.022,k,lod,math.radians(48) if tilted else 0.)
    w.bar(il-.008,ir+.008,iz-.005,it+.005,frame+.49,frame+.51,SHADOW,'shaded background')

def add_facade(b,lod=False):
    b.palette.update(PALETTE);first=len(b.parts)
    ox,oy,oz=PLACE['origin'];base=-oz+.012
    panels=SURVEY['panels']
    for row in panels:
        w=Face(b,row['from'],row['to'],row['label'])
        l,r,bottom,top=[row[k] for k in ('trim_left','trim_right','trim_bottom','trim_top')]
        holes=[box(l+.072,bottom+.052,r-.071,top-.073)]
        if row['lower_window_head_z'] is not None:
            head=row['lower_window_head_z'];holes.append(box(l+.076,head-.40,r-.076,head-.075))
        ztop=-1.295 if row is not panels[-1] else -1.226
        skin=box(0,base,w.width,ztop).difference(unary_union(holes))
        w.skin(skin,0,.28,BRICK,'running-bond masonry')
        window(w,row,lod)
        if row['lower_window_head_z'] is not None:
            w.bar(l,r,head-.082,head,-.034,.11,GREY,'lower window lintel')
            for a,c in [(l,l+.078),(r-.078,r)]:w.bar(a,c,head-.41,head-.077,-.034,.12,GREY,'lower jamb upper section')
            w.bar(l+.075,r-.074,head-.40,head-.071,.14,.155,GLASS[2],'lower window visible upper light')
            w.bar(l+.070,r-.070,head-.118,head-.076,.106,.153,WOOD,'lower light head')
        else:
            w.bar(0,w.width,ztop-.034,ztop+.045,-.152,.052,EDGE,'black drip and coping')
            w.bar(0,w.width,ztop+.036,ztop+.109,-.11,.303,GREY,'coping upper edge')
    # Short neutral return closures identify the row cut in the garden-side exhibit.
    for start,end in [((-1.097,3.07),(-1.098,1.122)),((6.92,1.186),(6.92,3.07)),((6.92,3.07),(-1.097,3.07))]:
        w=Face(b,start,end,'Extent of recorded frontage');w.bar(0,w.width,base,-1.17,.0,.11,BRICK,'plain return')
    b.plan_prism(Polygon([(2.837,1.193),(6.92,1.186),(6.92,3.07),(2.837,3.07)]),-1.21,-1.11,COVER,'Broad bay | roof closure')
    # The terrace module covers the projecting bay. Its slab begins above this cap.
    for p in b.parts[first:]:
        p['vertices']=[(x+ox,y+oy,z+oz)for x,y,z in p['vertices']]

def brick_uv(p):
    """Use metre-based UVs around all facets, including the oblique bay faces."""
    vertices=np.asarray(p['vertices']);coords=[];verts=[];faces=[];lookup={}
    for tri in p['triangles']:
        a,c,d=vertices[list(tri)];normal=np.cross(c-a,d-a);normal/=np.linalg.norm(normal)
        if abs(normal[2])>.8:s=(1.,0.,0.);t=(0.,1.,0.)
        else:
            s=np.array([-normal[1],normal[0],0.]);s/=np.linalg.norm(s);t=(0.,0.,1.)
        key=tuple(np.round(s,4))+tuple(t)
        f=[]
        for i in tri:
            pair=(i,key)
            if pair not in lookup:
                lookup[pair]=len(verts);v=vertices[i];verts.append(tuple(v));coords.append((v@s/.91,v@t/.52))
            f.append(lookup[pair])
        faces.append(tuple(f))
    p.update(vertices=verts,texcoords=coords,triangles=faces)
