"""Curved street masonry, windows cut through their reveals, and exterior stone dressings."""
import json
from collections import Counter
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parent
MEASURE = SOURCE.parent / 'measurements'
LAYOUT = json.loads((MEASURE/'street-frontage-layout.json').read_text())
SCHEDULE = json.loads((MEASURE/'street-window-schedule.json').read_text())['bays']
PLAN = np.array(LAYOUT['pier_tip_axes_m'])
VECTORS = np.diff(PLAN,axis=0)
LENGTH = np.linalg.norm(VECTORS,axis=1)
DIRECTIONS = VECTORS/LENGTH[:,None]
TANGENTS = np.vstack((DIRECTIONS[0], DIRECTIONS[:-1]+DIRECTIONS[1:], DIRECTIONS[-1]))
TANGENTS /= np.linalg.norm(TANGENTS,axis=1)[:,None]
DISTANCE = np.r_[0,np.cumsum(LENGTH)]
BRICK = 'Continental Court | red facing brick'
STONE = 'Continental Court | window and parapet aggregate'
EDGE = 'Continental Court | coping and sill nosing'
SHADE = 'Continental Court | recessed ashlar'
FLOWER = 'Continental Court | four-lobed relief'
BRICK_PERIOD = (1.428,.768)
PLAIN_FACE=.44
BACK=.83
BAND=LAYOUT['height_m']['band']

def material(rgb,texture=None):
    c=np.array(rgb)/255.
    result={'color':np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),'roughness':.89,'metallic':0.}
    if texture:
        result['texture']=str(SOURCE/texture)
    return result

PALETTE={BRICK:material([255,255,255],'continental-facing-brick.jpg'),
         STONE:material([166,159,142],'pier-aggregate.jpg'),
         EDGE:material([167,158,139]),SHADE:material([126,114,100]),FLOWER:material([138,129,105])}

class Bay:
    """u runs along a bay and d runs inward. World coordinates are east, north, up."""
    def __init__(self,index):
        self.index=index
        self.width=LENGTH[index]
        self.start=PLAN[index]
        self.t=DIRECTIONS[index]
        self.inside=np.array([-self.t[1],self.t[0]])
        # The measured upright axes and oriented tangents determine the sagitta of each bay.
        self.slopes=np.array([np.dot(v,self.inside)/np.dot(v,self.t) for v in TANGENTS[index:index+2]])

    def point(self,u,d,z):
        f=u/self.width
        m0,m1=self.slopes
        bend=self.width*(m0*f*(1-f)**2 + m1*f*f*(f-1))
        du=m0*(1-4*f+3*f*f)+m1*(3*f*f-2*f)
        normal=(self.inside-du*self.t)/np.sqrt(1+du*du)
        xy=self.start+self.t*u+self.inside*bend+normal*d
        return (xy[0],xy[1],z)

    def solid(self,builder,polygon,front,back,mat,label,cuts=()):
        """Triangulate both skins at the same curve stations. Only true perimeter edges get reveals."""
        if polygon.is_empty:return
        if polygon.geom_type!='Polygon':
            for part in polygon.geoms:
                if part.geom_type=='Polygon':self.solid(builder,part,front,back,mat,label,cuts)
            return
        if polygon.area<1.e-7:return
        xmin,zmin,xmax,zmax=polygon.bounds
        breaks=[xmin,*sorted({round(x,7)for x in cuts if xmin+1.e-5<x<xmax-1.e-5}),xmax]
        coords=[];index={};tri=[]
        def vertex(point):
            key=tuple(np.round(point[:2],7))
            if key not in index:
                index[key]=len(coords);coords.append(key)
            return index[key]
        for left,right in zip(breaks,breaks[1:]):
            part=polygon.intersection(box(left,zmin-1,right,zmax+1))
            for face in constrained_delaunay_triangles(part).geoms:
                if face.area<1.e-10:continue
                triangle=tuple(vertex(x)for x in orient(face,sign=1.).exterior.coords[:3])
                if len(set(triangle))==3:tri.append(triangle)
        if not tri:return
        vertices=[];local=[]
        for depth in [front,back]:
            for u,z in coords:
                d=depth(u)if callable(depth)else depth
                vertices.append(self.point(u,d,z))
                local.append([u,d,z])
        count=len(coords);edges=Counter();direction={}
        faces=list(tri)+[tuple(count+k for k in reversed(ids))for ids in tri]
        for ids in tri:
            for a,b in zip(ids,ids[1:]+ids[:1]):
                key=tuple(sorted((a,b)));edges[key]+=1;direction[key]=(a,b)
        for key,occurrences in edges.items():
            if occurrences==1:
                a,b=direction[key];faces.append((b,a,a+count,b+count))
        builder.add(vertices,faces,mat,'Street bay %02d | %s'%(self.index+1,label))
        if 'texture' in PALETTE[mat]:
            tile=BRICK_PERIOD if mat==BRICK else (.71,.71)
            self.uv(builder.parts[-1],np.array(local),tile)

    def uv(self,part,local,tile):
        # The front runs in street distance and true elevation. The returns wrap according
        # to their physical normal, which gives each window jamb actual nondegenerate UVs.
        coords=part['vertices'];mapping={};verts=[];uv=[];tri=[]
        bases=((1,2),(0,2),(0,1))
        for ids in part['triangles']:
            xyz=local[list(ids)];n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])
            axis=int(np.argmax(np.abs(n)));new=[]
            for k in ids:
                key=(k,axis)
                if key not in mapping:
                    mapping[key]=len(verts);verts.append(coords[k])
                    a,h=bases[axis]
                    uv.append(((local[k,a]+(DISTANCE[self.index] if a==0 else 0))/tile[0],local[k,h]/tile[1]))
                new.append(mapping[key])
            tri.append(tuple(new))
        part.update(vertices=verts,texcoords=uv,triangles=tri)

def rect(bay,b,left,right,low,high,front,back,mat,label,cuts=()):
    if right>left and high>low:bay.solid(b,box(left,low,right,high),front,back,mat,label,cuts)

def reveals(fields):
    return [box(l,row['sill_z'],r,row['head_z']) for row in fields for l,r in row['openings_u_m']]

def dressed_window(bay,b,row,l,r,lod):
    lo,hi=row['sill_z'],row['head_z'];d=row['face_depth_m']
    aperture=box(l,lo,r,hi)
    w=.115
    skin=box(l-w,lo-.080,r+w,hi+.145)
    # Staggered jamb blocks project to either side of the regular stone lining.
    blocks=[skin,box(l-w-.055,hi-.043,r+w+.055,hi+.18)]
    for at in [.24,.69]:
        z=lo+at*(hi-lo)
        blocks.extend([box(l-w-.095,z-.115,l+.018,z+.115),box(r-.018,z-.115,r+w+.095,z+.115)])
    bay.solid(b,unary_union(blocks).difference(aperture),d-.057,d+.028,STONE,'stepped window dressing')
    rect(bay,b,l-.15,r+.15,lo-.095,lo-.02,d-.114,d+.04,EDGE,'projecting sill')
    if not lod:
        rect(bay,b,l-.18,r+.18,lo-.055,lo-.018,d-.144,d-.10,STONE,'sill drip edge')

def flower_tile(bay,b,lod):
    x=bay.width*.5;z=8.26
    def diamond(r):return Polygon([(x,z+r),(x+r,z),(x,z-r),(x-r,z)])
    bay.solid(b,diamond(.276),.392,.452,EDGE,'diamond spandrel tile')
    bay.solid(b,diamond(.232).difference(diamond(.197)),.347,.402,STONE,'diagonal relief frame')
    if lod:
        unit=Polygon([(x-.104,z),(x-.044,z+.048),(x,z+.141),(x+.044,z+.048),(x+.104,z),
                      (x+.044,z-.048),(x,z-.141),(x-.044,z-.048)])
        bay.solid(b,unit,.33,.397,FLOWER,'four-lobed relief')
    else:
        for i in range(4):
            a=i*np.pi/2;c,s=np.cos(a),np.sin(a)
            leaf=np.array([[0,.012],[-.061,.081],[-.044,.135],[0,.167],[.044,.135],[.061,.081]])
            leaf=leaf@np.array([[c,s],[-s,c]])+[x,z]
            bay.solid(b,Polygon(leaf),.333,.395,FLOWER,'spandrel flower petal')
        bay.solid(b,diamond(.044),.316,.365,EDGE,'central flower boss')

def make_oriel(bay,b,rows,lod,cuts):
    # Three bays have projecting, dressed two-storey fronts above the shops.
    width=bay.width;left=.124*width;right=.876*width;shoulder=.215*width
    d=rows[0]['face_depth_m'];field=box(left,BAND-.015,right,12.59)
    outer=lambda u: d+(PLAIN_FACE-d)*max(0.,(shoulder-u)/(shoulder-left),(u-(width-shoulder))/(shoulder-left))
    bay.solid(b,field.difference(unary_union(reveals(rows[:2]))),outer,PLAIN_FACE+.036,STONE,
              'two-storey projecting ashlar bay',(*cuts,shoulder,width-shoulder))
    for z,projection,thickness in [(12.42,.08,.15),(12.55,.17,.15),(12.67,.25,.105)]:
        rect(bay,b,left-.06,right+.06,z,z+thickness,lambda u,p=projection:outer(u)-p,
             PLAIN_FACE+.075,EDGE,'projecting oriel cornice',(*cuts,shoulder,width-shoulder))
    for row in rows[:2]:
        l,r=row['openings_u_m'][0][0],row['openings_u_m'][-1][1];lo,hi=row['sill_z'],row['head_z']
        rect(bay,b,l-.094,r+.094,lo-.09,lo-.015,d-.150,d+.055,EDGE,'continuous triple-window sill')
        rect(bay,b,l-.105,r+.105,hi,hi+.16,d-.068,d+.04,STONE,'triple-window head')
        if row['floor']==2:
            centre=(l+r)/2
            outline=[(l-.08,hi+.08),(r+.08,hi+.08),(r+.08,hi+.18),(centre+.43,hi+.18),
                     (centre+.43,hi+.40),(centre+.24,hi+.40),(centre+.24,hi+.65),
                     (centre-.24,hi+.65),(centre-.24,hi+.40),(centre-.43,hi+.40),(centre-.43,hi+.18),(l-.08,hi+.18)]
            bay.solid(b,Polygon(outline),d-.10,d+.035,STONE,'stepped central keystone')
    if not lod:
        for z in [7.98,8.44,8.90,11.89,12.34]:
            rect(bay,b,left+.16,right-.16,z,z+.013,lambda u:outer(u)-.006,lambda u:outer(u)+.002,SHADE,'ashlar bed joint',cuts)

def parapet(bay):
    key='covered_east_and_centre' if bay.index<7 else 'open_southern_bays'
    section=LAYOUT['parapet_sections'][key]
    centres=bay.width/2+np.array([-1.5,-.5,.5,1.5])*1.015+section['notch_axis_offset_m']
    if bay.index==4:
        centres=np.linspace(1.261,4.302,4)
    return section,centres

def street_wall(b, lod=False):
    for record in SCHEDULE:
        bay=Bay(record['bay']);width=bay.width;rows=record['floors'];cuts=np.linspace(0,width,7 if lod else 13)[1:-1]
        # The upper brick edge is castellated, including its shorter end crenels.
        section,notch_axis=parapet(bay)
        low,high=section['base_and_coping_top_m']
        half=section['half_notch_width_m']
        cap_front=section['coping_front_inward_m']
        low_wall=box(0,BAND-.025,width,low)
        gaps=[box(u-half,low-1.e-3,u+half,high+.001)for u in notch_axis]
        merlons=box(0,low-.002,width,high).difference(unary_union(gaps))
        wall=unary_union([low_wall,merlons]).difference(unary_union(reveals(rows)))
        bay.solid(b,wall,PLAIN_FACE,BACK,BRICK,'pierced red-brick facade',cuts)
        edges=[0.,*[v for u in notch_axis for v in (u-half,u+half)],width]
        for l,r in zip(edges[::2],edges[1::2]):
            rect(bay,b,l,r,high-.125,high+.013,cap_front,.853,STONE,'merlon coping',cuts)
        for u in notch_axis:
            for lo,hi in [(u-half-.109,u-half),(u+half,u+half+.109)]:
                rect(bay,b,lo,hi,low-.11,high-.088,cap_front-.004,.454,STONE,'parapet notch cheek')
            rect(bay,b,u-half-.109,u+half+.109,low-.11,low+.003,cap_front-.016,.855,STONE,'parapet notch sill')
            if section['strip_centre_z_m'] is not None:
                z=section['strip_centre_z_m']
                rect(bay,b,u-half-.015,u+half+.015,z-.013,z+.013,.469,.509,SHADE,'bridging strip above square opening')
        # Moulded string and masonry dentils below the highest storey.
        for z,dep,h in [(12.61,.30,.17),(12.79,.245,.11),(12.91,.317,.085)]:
            rect(bay,b,0,width,z,z+h,dep,PLAIN_FACE+.055,EDGE,'upper string coursing',cuts)
        if not lod:
            for u in np.arange(.16,width-.15,.225):
                rect(bay,b,u,u+.103,12.53,12.65,.343,.456,STONE,'string-course dentil')
        if rows[0]['configuration']=='three-light':
            make_oriel(bay,b,rows,lod,cuts)
            top=rows[2];l,r=top['openings_u_m'][0][0],top['openings_u_m'][-1][1]
            dressed_window(bay,b,top,l,r,lod)
            for first,second in zip(top['openings_u_m'],top['openings_u_m'][1:]):
                rect(bay,b,first[1],second[0],top['sill_z'],top['head_z'],PLAIN_FACE-.042,PLAIN_FACE+.073,STONE,'stone light mullion')
        else:
            for row in rows:
                for l,r in row['openings_u_m']:dressed_window(bay,b,row,l,r,lod)
            if bay.index in (1,2,3,4,7,8,9):flower_tile(bay,b,lod)

def add_street_front(builder,lod=False):
    """Build the masonry and install every sash in its actual clear opening."""
    from continental_window_sashes import add_sash
    street_wall(builder,lod)
    for record in SCHEDULE:
        bay=Bay(record['bay'])
        for row in record['floors']:
            for i,(l,r) in enumerate(row['openings_u_m']):
                add_sash(builder,lod,bay.point,bay.index,row['floor'],i,l,r,row['sill_z'],row['head_z'],
                         recess=row['face_depth_m']+row['sash_recess_m'],
                         strip_index=i if row['configuration']=='three-light' else None)
