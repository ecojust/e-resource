"""The gabled 2015 street facade at Jingxing Road lane 314, in the registered photograph plane."""
from math import cos, sin, radians, pi
from pathlib import Path
import json
import numpy as np
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
RED='314 | red brick in pale mortar'
GABLE='314 | washed red bricks'
BROWN='314 | dark base bricks'
STONE='314 | light render'
CAP='314 | aged coping'
TIMBER='314 | dark red timber'
GLASS='314 | dull window glass'
DEEP='314 | inside reveal'
IRON='314 | painted iron'
GREEN='314 | green sheet metal'
GREY='314 | grey steel shutter'
BLUE='314 | blue steel shutter'
BASE='314 | patched basement render'
PIPE='314 | pale rainwater pipe'
SASH='314 | replacement white frame'

def colour(rgb,roughness=.87):
    return {'color':[((v/255+.055)/1.055)**2.4 if v>10.31475 else v/(255*12.92) for v in rgb],'roughness':roughness}

PALETTE={RED:{'texture':str(HERE/'yiqingli-scarlet-brick.png'),'color':[1.,1.,1.],'roughness':.94},
 GABLE:{'texture':str(HERE/'yiqingli-gable-wash.png'),'color':[1.,1.,1.],'roughness':.96},
 BROWN:{'texture':str(HERE/'yiqingli-base-brick.png'),'color':[1.,1.,1.],'roughness':.96},
 STONE:colour((190,180,152)),CAP:colour((106,101,87)),TIMBER:colour((125,56,42)),
 GLASS:colour((108,120,119),.35),DEEP:colour((49,45,41)),IRON:colour((74,71,60),.58),
 GREEN:colour((74,108,82),.69),GREY:colour((131,132,122),.66),BLUE:colour((63,98,142),.60),
 BASE:{'texture':str(HERE/'yiqingli-limewash.png'),'color':[1.,1.,1.],'roughness':.97},
 '314 | terracotta patch':colour((174,117,84)),PIPE:colour((192,182,157)),SASH:colour((198,195,173),.66)}

class Front:
    def __init__(self,b,layout):
        self.b=b
        self.k=layout['metres_per_reference_pixel']
        self.left=layout['front_left_px']
        self.grade=layout['grade_px']
    def x(self,u):return (u-self.left)*self.k
    def z(self,v):return (self.grade-v)*self.k
    def poly(self,points):return Polygon([(self.x(u),self.z(v)) for u,v in points])
    def rect(self,u,v,r,t):return box(self.x(u),self.z(t),self.x(r),self.z(v))
    def panel(self,shape,back,front,material,label):
        if not shape.is_empty:
            self.b.prism(shape,back,front,lambda x,z,d:(x,-d,z),material,'314 '+label)
    def strip(self,pts,width_px,back,front,mat,label):
        line=LineString([(self.x(u),self.z(v)) for u,v in pts])
        self.panel(line.buffer(width_px*self.k/2,cap_style=2,join_style=2),back,front,mat,label)
    def bar(self,u,d,v,u1,d1,v1,r,mat,label,lod):
        self.b.tube([(self.x(u),-d,self.z(v)),(self.x(u1),-d1,self.z(v1))],r,mat,6 if lod else 10,'314 '+label)
    def block(self,u,v,r,t,back,front,material,label):
        self.panel(self.rect(u,v,r,t),back,front,material,label)
    def local_box(self,center,size,material,label,basis=None):
        self.b.box(center,size,material,basis,'314 '+label)

def closed_sash(w,a,columns,rows,frame,label,lod):
    x,y,r,t=a
    shape=w.rect(*a)
    w.panel(shape,-.226,-.204,GLASS,label+' recessed glazing')
    rail=.052
    holes=[]
    cellx=(r-x)/columns;celly=(t-y)/rows
    for i in range(columns):
        for j in range(rows):
            holes.append(w.rect(x+i*cellx+rail/w.k/2,y+j*celly+rail/w.k/2,
                               x+(i+1)*cellx-rail/w.k/2,y+(j+1)*celly-rail/w.k/2))
    w.panel(shape.difference(unary_union(holes)),-.205,-.142,frame,label+' dividing frame')

def hinged_leaf(w,u,v,t,width,angle,sign,filled,lod,label,frame=TIMBER,depth=.12):
    # Starting from the jamb, the opening motion has its own hinge and depth.
    a=radians(angle);horizontal=np.array([sign*cos(a),-sin(a),0.])
    normal=np.array([sin(a),sign*cos(a),0.])
    up=np.array([0.,0.,1.])
    origin=np.array([w.x(u),depth,w.z(t)])
    h=(t-v)*w.k
    def bar(x,d,z,b,thick,high,mat,part):
        w.local_box(origin+x*horizontal+d*normal+z*up,(b,thick,high),mat,label+' '+part,[horizontal,normal,up])
    for x in [.025,width-.025]:
        bar(x,0,h/2,.05,.066,h,frame,'stile')
    for z in [0,h*.25,h*.50,h*.75,h]:
        bar(width/2,0,z,width,.069,.042,frame,'putty rail')
    bar(width/2,-.005,h/2,.036,.055,h,frame,'mullion')
    for col in range(2):
        for row in range(4):
            if (col,row) not in filled:continue
            bar((col+.5)*width/2,.015,(row+.5)*h/4,width/2-.035,.021,h/4-.037,GLASS,'glass pane')
    if not lod:
        for z in [h*.16,h*.84]:
            w.local_box(origin+up*z,(.056,.068,.14),IRON,label+' hinge')

def tall_windows(w,A,lod):
    for idx,key in enumerate(['tall_left','tall_right']):
        a=A[key];x,y,r,t=a;label='paired tall sash '+str(idx+1)
        w.panel(w.rect(x-50,y-28,r+50,t+28),-.710,-.684,DEEP,label+' recessed inner shadow')
        for u in [x+1.15,r-1.15]:
            w.block(u-1.25,y,u+1.25,t,-.155,-.082,TIMBER,label+' jamb')
        w.block(x,y,r,y+2.7,-.16,-.08,TIMBER,label+' lintel frame')
        mid=y+33
        w.block(x,mid-1.2,r,mid+1.2,-.12,-.046,TIMBER,label+' transom bar')
        w.block((x+r)/2-1.2,y,(x+r)/2+1.2,mid,-.14,-.061,TIMBER,label+' transom mullion')
        for j in range(2):
            x0=x+j*(r-x)/2+2; x1=x+(j+1)*(r-x)/2-2
            w.block(x0,y+2,x1,mid-2,-.233,-.215,DEEP,label+' dark transom')
        if idx==0:
            width=(r-x)*w.k/2
            panes={(col,row) for col in range(2) for row in range(4)}
            hinged_leaf(w,x+2,mid+1,t-1,width,4,1,panes-{(1,2),(1,1)},lod,label+' left leaf')
            fit=json.loads((HERE.parent/'measurements/314-open-casement.json').read_bytes())
            hinged_leaf(w,fit['hinge_registered_u'],fit['sash_head_registered_v'],
                        fit['sash_foot_registered_v'],fit['leaf_width_m'],fit['outward_angle_deg'],
                        -1,panes,lod,label+' outward leaf',depth=fit['hinge_depth_m'])
        for margin,va,vb,d in [(7,y-20,y-6,.17),(12,y-22,y-18,.23),(5,y-7,y-3,.13)]:
            w.block(x-margin,va,r+margin,vb,-.012,d,STONE,label+' projecting head')
        for margin,va,vb,d in [(7,t+1,t+5,.25),(4,t+5,t+9,.20),(1,t+9,t+12,.13)]:
            w.block(x-margin,va,r+margin,vb,-.03,d,STONE,label+' sill profile')
        if idx==0:
            # A shallow folded green hood survives only on the left head.
            w.bar(x-10,.59,y+22,r+5,.59,y+12,.020,IRON,label+' awning edge',lod)
            profile=Polygon([(-.04,w.z(y)),(-.62,w.z(y+19)),(-.62,w.z(y+17)),(-.04,w.z(y-2))])
            w.b.prism(profile,w.x(x-11),w.x(r+1),lambda d,z,s:(s,d,z),GREEN,'314 '+label+' curved shade')
        if not lod:
            w.bar(x+19,.15,t+11,x+19,.15,t+28,.017,IRON,label+' old rack bracket',lod)
            w.bar(x+19,.15,t+28,r-5,.51,t+14,.016,IRON,label+' old rack bracket',lod)

def roller(w,a,mat,label,lod):
    x,y,r,t=a
    w.block(x,y,r,t,-.138,-.103,mat,label+' roller shutter')
    # Visibly different finishes on the two bays, with a rolled profile at full detail.
    count=max(5,round((t-y)/(7.0 if lod else 3.3)))
    for k in range(count):
        v=y+(k+.60)*(t-y)/count
        w.block(x+.8,v,r-.8,v+(.65 if lod else .70),-.113,-.086,mat,label+' shutter rib')
    for u in [x+.4,r-.4]:
        w.block(u-.9,y,u+.9,t,-.15,-.065,IRON,label+' side channel')

def awnings(w,lod):
    # The sheet-metal awning is patched in sections with irregular leading edges.
    bays=[(292,353,.74,7),(355,422,.64,8),(424,519,.83,9),(521,580,.68,8),
          (589,635,.93,6),(638,686,.79,7),(689,746,.76,6),(749,810,.62,7)]
    for i,(x,r,depth,n) in enumerate(bays):
        count=n if not lod else max(3,n//2)
        for k in range(count):
            u=x+(r-x)*k/count;end=x+(r-x)*(k+1)/count
            v=517+(2 if i in [0,5] else 0)
            h=w.z(v);l=depth*1.22-(.07 if (i+k)%7==0 else 0)
            a=np.array([w.x(u),-.05,h]);front=np.array([0.,-l,-.17])
            across=np.array([w.x(end)-w.x(u),0,0]);wave=.022
            vertices=[a,a+across/2+[0,0,wave],a+across,a+front,
                      a+across/2+front+[0,0,wave],a+across+front]
            vertices+=[v0-[0,0,.018] for v0 in vertices]
            w.b.add(vertices,[(0,3,4,1),(1,4,5,2),(6,7,10,9),(7,8,11,10),
                              (0,1,7,6),(1,2,8,7),(2,5,11,8),(5,4,10,11),
                              (4,3,9,10),(3,0,6,9)],GREEN,'314 corrugated shop canopy')
        for u in [x+2,r-2]:
            w.bar(u,.04,v+6,u,depth-.02,v+9,.018,IRON,'awning support',lod)

def add_front(b,lod=False,layout=None):
    data=json.loads((HERE/'facade314-layout.json').read_bytes())
    if layout:data.update(layout)
    w=Front(b,data);A=data['bays']
    outline=w.poly(data['top_outline']+[[1062,w.grade],[72,w.grade]])
    holes=unary_union([w.rect(*a) for a in A.values()])
    wall=outline.difference(holes)
    w.panel(wall,-.42,0,RED,'continuous wall with ten cut apertures')
    # Distinct washed brick in the crown contrasts with the bright joints by the left eave.
    gable=w.poly([[337,242],[374,239],[374,217],[573,109],[573,78],[663,78],[668,109],[872,211],[881,241],[907,243],[907,272],[666,277],[336,276]])
    w.panel(wall.intersection(gable),.001,.012,GABLE,'washed central gable face')
    band=w.poly(data['top_outline'][1:-1]+list(reversed(data['gable_band_inner'])))
    if not band.is_valid:band=band.buffer(0)
    w.panel(band.intersection(outline),.013,.089,STONE,'broad gable edge')
    w.strip(data['top_outline'][1:-1],4.2,-.10,.157,CAP,'dark gable coping')
    for y,t in [(276,293),(385,413),(483,505)]:
        w.panel(wall.intersection(w.rect(72,y,1062,t)),.011,.028,STONE,'light belt '+str(y))
    w.panel(wall.intersection(w.rect(72,526,398,695)),.005,.016,BROWN,'dark shop base brick')
    w.panel(wall.intersection(w.rect(72,618,1062,698)),.017,.033,BASE,'patched plinth')
    for label in ['small_upper','mezzanine','small_ground']:
        a=A[label];x,y,r,t=a
        closed_sash(w,a,2,2 if label=='small_upper' else 1,TIMBER,label,lod)
        w.block(x-5,y-5,r+5,y-1,-.01,.135,CAP,label+' thin head')
        w.block(x-5,t+1,r+4,t+4,-.01,.188,STONE,label+' sill')
    x,y,r,t=A['small_upper']
    for lo,hi in [(x-3,x+3.5),(r-4,r+3)]:
        w.block(lo,y,hi,t,-.18,.034,STONE,'upper window lined reveal')
    w.block(x-6,y-2,r+8,y+1,-.02,.45,STONE,'upper window pale hood')
    for v in [t+1,t+4]:
        w.bar(x-41,.49,v,r+48,.49,v,.015,IRON,'wide sill drying rack',lod)
    for u in [x-31,x+4,r-2,r+37]:
        w.bar(u,.02,t+2,u,.50,t+2,.019,IRON,'wide steel rack arm',lod)
        if not lod:w.bar(u,.02,t+12,u,.49,t+2,.012,IRON,'sill rack brace',lod)
    for patch in [[[746,635],[760,634],[762,647],[780,648],[774,668],[743,669]],
                  [[793,626],[820,624],[817,655],[828,666],[805,674],[783,665]],
                  [[666,664],[676,659],[702,662],[713,678],[691,682],[669,679]]]:
        w.panel(w.poly(patch).intersection(wall),.034,.038,'314 | terracotta patch','worn lower plaster patch')
    w.block(195,550,247,696,-.190,-.142,TIMBER,'ground door with recessed frame')
    closed_sash(w,A['replacement_fanlight'],3,1,SASH,'replacement upper light',lod)
    w.panel(w.rect(*A['east_lower']),-.48,-.443,DEEP,'dark lower east opening')
    w.block(628,480,657,614,-.26,-.21,TIMBER,'lower east surviving sash')
    w.block(620,617,731,623,-.012,.149,STONE,'east lower sill')
    roller(w,A['roller_grey'],GREY,'narrow grey',lod)
    roller(w,A['roller_blue'],BLUE,'broad blue',lod)
    tall_windows(w,A,lod)
    awnings(w,lod)
    for name,profile in [('left',[(359,.08,232),(354,.07,410),(283,.09,481),(283,.09,520)]),
                         ('right',[(916,.16,226),(908,.12,245),(908,.10,504),(899,.10,544),(899,.10,690)])]:
        b.tube([(w.x(u),-d,w.z(v)) for u,d,v in profile],.052,PIPE,8 if lod else 12,'314 '+name+' rainwater pipe')
        for u,d,v in profile[1:]:
            w.block(u-3,v-1,u+3,v+1,-.015,d+.065,PIPE,name+' rainwater collar')
    for u,r,v in [(74,349,229),(919,1061,221)]:
        w.bar(u,.07,v,r,.07,v,.075,PIPE,'half-round eaves gutter',lod)
