"""Two measured storeys at the Huaya Hall shutter wall, including its faceted return."""
import json
from pathlib import Path

import numpy as np
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import pediment_windows as windows

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE.parent/'measurements/three-visible-wall-planes.json').read_text())
CORNERS=np.array(DATA['plane_outline_xy_m'])
SLOTS=DATA['plaster_openings_in_face_coordinates']
FIELD='Wall | pale scored render'
LIGHT='Wall | light raised moulding'
SHADE='Wall | grey-brown cut edge'
BASE='Wall | dark grey plinth'
RECESS='Wall | shaded reveals'
RED='Bay | oxblood painted shutters'
GLASS='Bay | dark window glass'
GREEN='Bay | grey service metal'
PALETTE={k:windows.finish(c,r) for k,c,r in [
    (FIELD,(196,192,177),.94),(LIGHT,(211,204,182),.88),(SHADE,(145,138,118),.9),
    (BASE,(130,119,106),.91),(RECESS,(103,97,88),.94),(RED,(107,53,49),.81),
    (GLASS,(52,65,66),.31),(GREEN,(131,144,143),.81)]}
PALETTE[RED].update(texture=str(HERE/'huaya-painted-timber.jpg'),color=[.79,.74,.72])
PALETTE[LIGHT].update(texture=str(HERE/'huaya-cast-stone.jpg'),color=[1.,1.,.98])

class Facade:
    def __init__(self,b,index):
        self.b=b;self.index=index;self.start=CORNERS[index];d=CORNERS[index+1]-self.start
        self.length=np.linalg.norm(d);self.u=d/self.length;self.n=np.array([-self.u[1],self.u[0]])
        self.label=['Three-window wall','Angled bay','Forward bay'][index]
    def xyz(self,x,y,z):
        a=self.start+x*self.u+y*self.n
        return [*a,z]
    def solid(self,poly,front,back,material,name):
        if poly.is_empty:return
        if poly.geom_type!='Polygon':
            for sub in poly.geoms:self.solid(sub,front,back,material,name)
            return
        if poly.area<.000001:return
        self.b.prism(orient(poly,sign=1),-back,-front,lambda x,z,d:self.xyz(x,-d,z),material,self.label+' | '+name)
    def rect(self,l,r,b,t,front,back,material,name):
        if r>l and t>b:self.solid(box(l,b,r,t),front,back,material,name)
    def local_part(self,part,scale,offset,title):
        v=np.asarray(part['vertices'])*np.asarray(scale)+np.asarray(offset)
        part['vertices']=[self.xyz(x,y,z) for x,y,z in v]
        part['label']=title+' | '+part['label'].split(' | ',1)[-1]
    def cornice(self,l,r,z,top,lod):
        # Flat soffit with large square dentils; below it runs a second row of much smaller beads.
        for i,(lo,hi,depth) in enumerate([(0,.047,.052),(.050,.084,.076),(.088,.123,.092),(.166,.215,.136),(.222,.261,.103),(.382,.419,.240),(.421,.457,.284),(.463,.518,.272),(.524,.568,.220)]):
            self.rect(l-.017,r+.017,z+lo*top,z+hi*top,-depth,.044,LIGHT if i not in (2,5) else SHADE,'cornice course %02d'%(i+1))
        for tag,pitch,width,bottom,height,depth in [('square dentil',.286,.129,.254,.13,.195),('small bead',.104,.053,.112,.062,.104)]:
            count=max(1,round((r-l)/pitch));step=(r-l)/count
            for i in range(count):
                x=l+step*(i+.5)
                self.rect(x-width/2,x+width/2,z+bottom*top,z+(bottom+height)*top,-depth,-.019,LIGHT,f'{tag} {i+1:03d}')
    def field(self,outline,holes,lod):
        # A recessed backing remains behind every 6 mm wide flush horizontal joint.
        cut=unary_union(holes);body=outline.difference(cut)
        self.solid(body,.027,.276,FIELD,'wall core and opening sides')
        lim=outline.bounds;zs=np.arange(-1.72,10.90,.443)
        for i,(z,t) in enumerate(zip(zs,zs[1:])):
            strip=body.intersection(box(lim[0],z+.003,lim[2],t-.003))
            # The widely spaced vertical joints alternate by course.
            grid=np.arange(-3.+(i%2)*.893,lim[2]+2.1,1.786)
            for k,(l,r) in enumerate(zip(grid,grid[1:])):
                tile=strip.intersection(box(l+.002,z,r-.002,t))
                self.solid(tile,0,.045,FIELD,f'ashlar course {i+1:02d} panel {k+1:02d}')

def cap_profile(c,z,rx,rz,steps):
    theta=np.linspace(np.pi,0,steps)
    return [(c+rx*np.cos(a),z+rz*np.sin(a)) for a in theta]

def upper_window(face,row,lod):
    l,r,b,t=(row[k]for k in ('left','right','bottom','top'));c=(l+r)/2;wid=r-l
    arch=row['arch_crown'];rx=.5*wid+.335;rz=arch-t-.36
    face.rect(l-.25,r+.25,b-.126,b,-.173,.070,LIGHT,'upper projecting sill')
    # Stepped apron with the pair of square drops at opposite ends of the sill.
    face.solid(Polygon([(l-.18,b-.13),(r+.18,b-.13),(r+.18,b-.46),(r-.035,b-.46),(r-.035,b-.35),(l+.04,b-.35),(l+.04,b-.46),(l-.18,b-.46)]),-.055,.018,LIGHT,'notched apron below upper sill')
    for side,edge in [(-1,l),(1,r)]:
        x=edge+side*.12
        face.rect(x-.11,x+.11,b+.01,t+.19,-.13,.06,LIGHT,'upper pilaster shaft')
        face.rect(x-.155,x+.155,t+.12,t+.21,-.176,.027,LIGHT,'upper pilaster collar')
        face.rect(x-.182,x+.182,t+.221,t+.319,-.201,.039,LIGHT,'upper impost and cap')
    face.rect(l-.28,r+.28,t+.13,t+.36,-.168,.048,LIGHT,'upper lintel with plain soffit')
    n=25 if lod else 43
    bed=Polygon([*cap_profile(c,t+.31,rx,rz,n),(c-rx,t+.31)])
    face.solid(bed,-.091,.035,LIGHT,'round overdoor field')
    for i,(w,h,d) in enumerate([(0,0,.194),(.048,.054,.171),(.097,.108,.144)]):
        outer=cap_profile(c,t+.31,rx-w,rz-h,n);inner=cap_profile(c,t+.31,rx-w-.035,rz-h-.036,n)
        face.solid(Polygon(outer+inner[::-1]),-d,-.078,LIGHT,'concentric arch band '+str(i+1))
    # Short axial beads on the top half of the round head and its carved central cartouche.
    for i,a in enumerate(np.linspace(.22,np.pi-.22,15 if lod else 29)):
        x=c+(rx-.142)*np.cos(a);z=t+.315+(rz-.158)*np.sin(a)
        p=Polygon([(x-.022,z-.028),(x+.012,z-.033),(x+.022,z+.026),(x-.008,z+.035)])
        face.solid(p,-.154,-.079,LIGHT,'arch dentil '+str(i+1))
    crest=Polygon([(c-.13,t+.42),(c-.17,t+.56),(c-.09,t+.70),(c,t+.65),(c+.09,t+.70),(c+.17,t+.56),(c+.13,t+.42),(c,t+.40)])
    face.solid(crest,-.184,-.085,LIGHT,'central relief shield')
    for sign in (-1,1):
        v=[(c+sign*x,t+.40+z)for x,z in [(.09,.10),(.23,.17),(.34,.13),(.39,.065),(.32,.04),(.28,.076)]]
        face.solid(LineString(v).buffer(.019,join_style='round'),-.172,-.083,LIGHT,'flanking scroll')
    framing(face,l,r,b,t,.26)
    # Shutters project from their edge hinges. Both faces in the near photograph have open red leaves.
    for index,edge_record in enumerate(row['free_edges']):
        side=edge_record['side'];wr=edge_record['width_m'];angle=np.deg2rad(edge_record['angle_degrees'])
        edge=l if side=='left' else r;sign=1 if side=='left' else -1
        depth=edge_record['hinge_inset_m']
        co=np.cos(angle);si=np.sin(angle)
        moving_top=t if face.index==1 else b+(t-b)*.79
        def turn(x,y,z):
            return face.xyz(edge+sign*x*co+y*si,depth-x*si+y*sign*co,z)
        for a,bb,lo,hi,mat,name in [(0,.054,b+.012,moving_top-.02,RED,'hinge stile'),(wr-.056,wr,b+.012,moving_top-.02,RED,'edge stile'),(.052,wr-.053,b+.011,b+.117,RED,'bottom rail'),(.052,wr-.053,moving_top-.126,moving_top-.02,RED,'top rail'),(.052,wr-.053,b+1.06,b+1.16,RED,'mid rail')]:
            face.b.prism(orient(box(a,lo,bb,hi),sign=1),-.038,0,lambda x,z,y:turn(x,-y,z),mat,face.label+' | '+name+str(index+1))
        if face.index==1:
            for z0,z1 in [(b+.112,b+1.055),(b+1.161,moving_top-.13)]:
                face.b.prism(orient(box(.055,z0,wr-.054,z1),sign=1),-.018,-.011,lambda x,z,y:turn(x,-y,z),GLASS,face.label+' | opened glazed casement')
            continue
        for i,z in enumerate(np.arange(b+.159,moving_top-.15,.081)):
            if b+1.04<z<b+1.20:continue
            yz=np.array([[-.018,z-.029],[.018,z+.012],[.018,z+.033],[-.018,z-.008]])
            vertices=[turn(x,y,zz)for x in (.052,wr-.052)for y,zz in yz]
            tri=[[0,3,2,1],[4,5,6,7]]+[[j,(j+1)%4,(j+1)%4+4,j+4]for j in range(4)]
            face.b.add(vertices,tri,RED,face.label+f' | open upper shutter {index+1} blade {i+1:02d}')
def framing(face,l,r,b,t,depth):
    c=(l+r)/2;mid=b+(t-b)*.67
    face.rect(l,r,b,t,depth+.05,depth+.102,GLASS,'shaded window pane')
    for x in (l,c,r):face.rect(x-.026,x+.026,b,t,depth-.014,depth+.05,RED,'fixed window upright')
    for z in (b,mid,t):face.rect(l,r,z-.031,z+.031,depth-.03,depth+.051,RED,'fixed window rail')

def lower_window(face,row,lod):
    l,r,b,t=(row[k]for k in ('left','right','bottom','top'));c=(l+r)/2
    xscale=(r-l)/1.28;zscale=(t-b)/2.67
    # The shallow recesses and dark splayed openings remain part of the main wall.
    face.rect(l-.015,r+.015,b-.02,t+.02,.60,.65,RECESS,'lower window dark backing')
    start=len(face.b.parts)
    for i in ((1,2) if face.index==1 else range(4)):
        windows.shutter(face.b,0,'Lower shutter '+str(i+1),i,lod)
    for side in (-1,1):windows.pilaster(face.b,0,'Side window',side,lod)
    windows.pediment(face.b,0,'Projected window',lod)
    for part in face.b.parts[start:]:
        v=np.array(part['vertices'])
        if 'shutter' in part['label'].lower():
            v[:,1]+=.17 if face.index==1 else .33
            if face.index==1:v[:,0]*=2.0
        lateral=v[:,0].copy();distance=np.abs(lateral)
        v[:,0]=np.sign(lateral)*np.where(distance<=.64,distance*xscale,.64*xscale+(distance-.64)*.86)
        if v[:,2].max()>2.80:
            cap=row['pediment_top']-b
            v[:,2]=np.where(v[:,2]>2.70,2.70+(v[:,2]-2.70)*(cap/zscale-2.70)/(.955),v[:,2])
        part['vertices']=v.tolist()
        face.local_part(part,[1,1,zscale],[c,0,b],face.label+' lower window')
    face.rect(l-.29,r+.29,b-.14,b,-.16,.04,LIGHT,'continuous lower sill and nose')
    # Carved rectangle, inset lozenge and two end ornaments surviving below the shutter sill.
    for z in (b-.78,b-.41):face.rect(l+.02,r-.02,z,z+.041,-.064,.012,LIGHT,'relief panel rail')
    xy=[(c,b-.45),(c+.13,b-.585),(c,b-.72),(c-.13,b-.585),(c,b-.45)]
    face.solid(LineString(xy).buffer(.026,join_style='mitre'),-.090,-.006,LIGHT,'apron diamond')

def add_visible_walls(b,lod=False):
    for idx in range(3):
        face=Facade(b,idx);length=face.length
        top=10.56;zmin=-1.62
        outline=box(0,zmin,length,top)
        if idx==0:outline=outline.difference(box(-1,4.961,4.7,top+.2))
        cutoff=[(l+3.78,r+3.78,bt,tp)for l,r,bt,tp in windows.openings()]if idx==0 else []
        more=[row for row in SLOTS if row['face']==idx]
        for row in more:cutoff.append(tuple(row[k]for k in ('left','right','bottom','top')))
        if idx==0:cutoff.append((5.29,6.91,6.07,9.32))
        holes=[box(l-.007,bt-.006,r+.007,tp+.009)for l,r,bt,tp in cutoff]
        face.field(outline,holes,lod)
        face.rect(.0,length,-1.57,-1.43,-.055,.042,BASE,'red-grey plinth course')
        face.cornice(0,length,4.397,1.,lod)
        face.cornice(4.7 if idx==0 else 0,length,10.07,.89,lod)
        if idx==0:
            for l,r,bt,tp in cutoff[:3]:
                face.rect(l-.47,r+.47,-.14,-.007,-.163,.021,LIGHT,'ground level sill')
            c=2.4+3.78
            for z in (-.69,-.395):face.rect(c-.64,c+.59,z,z+.041,-.067,.018,LIGHT,'visible lower apron band')
            diamond=[(c,-.40),(c+.15,-.535),(c,-.67),(c-.15,-.535),(c,-.40)]
            face.solid(LineString(diamond).buffer(.022,join_style='mitre'),-.086,-.011,LIGHT,'visible lower apron diamond')
            framing(face,5.29,6.91,6.07,9.32,.22)
            face.rect(5.08,7.13,5.88,6.06,-.175,.035,LIGHT,'upper straight sill')
            for station,z in [(7.76,6.75),(8.88,6.30)]:
                face.rect(station-.41,station+.41,z,z+.53,-.36,.018,GREEN,'wall mounted condenser')
                for q in np.arange(z+.055,z+.485,.042):
                    face.rect(station-.32,station+.32,q,q+.013,-.383,-.34,RECESS,'condenser grille')
        for row in more:
            if row['level']=='upper':upper_window(face,row,lod)
            else:lower_window(face,row,lod)
