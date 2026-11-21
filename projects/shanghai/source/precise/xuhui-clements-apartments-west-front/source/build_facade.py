"""The two projecting street wings and recessed court of the west block, Lane 1363."""
from pathlib import Path
import math
import json
import sys
import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening

P=json.loads((HERE/'parameters.json').read_bytes())
META=dict(id=P['id'],name=P['name'],scope=P['scope'],status='photo-informed-exterior',
    audit_directory='data/audit/clements-apartments-west-front-v1/', viewer_page='clements-apartments-west-front.html',
    model_scope_zh='复兴中路1363弄内，西前楼朝街两翼、内凹墙面、明暗交替的砖饰、钢窗、坡瓦、成组烟囱和凹院沿街矮墙。楼后的四幢、共用弄门、住户内部与原有租户店招保留为待考范围。',
    coordinate_convention=P['source_frame'],interiors_modeled=False)
COLORS={
    'warm pebble render':(.779,.735,.652),'pale carved lintel':(.748,.694,.601),
    'claret face brick':(.512,.280,.224),'rust decoration':(.593,.327,.255),'sienna headers':(.568,.292,.235),
    'shadow red brick':(.422,.225,.192),'grey street plinth':(.445,.452,.445),'stone sill':(.605,.576,.528),
    'iron window grid':(.138,.167,.163),'recessed green glass':(.213,.278,.271),'dark weathered wood':(.258,.218,.188),
    'street door paint':(.255,.324,.310),'dull lead gutter':(.312,.319,.286),'tile terracotta':(.522,.308,.249),
    'burnt clay':(.452,.274,.222),'chimney pot':(.593,.381,.288),'flue opening':(.198,.167,.151),
}
PALETTE={k:dict(color=list(v),roughness=.33 if 'glass' in k else .86) for k,v in COLORS.items()}
FRONT=np.asarray(P['street_path_xy']);DEPTH=P['north_return_cut_m'];EAVE=13.78;PEAK=16.38

def steel(face,shape,low=False,arched=False):
    """Place the dark glazing behind an actual opening and a separate steel sash."""
    l,b,r,t=shape.bounds
    face.prism(shape,-.23,-.209,'recessed green glass','glazing behind reveal')
    bars=[shape.difference(shape.buffer(-.07,join_style='mitre'))]
    for ratio in ([.5] if low else [.25,.5,.75]):
        x=l+(r-l)*ratio;bars.append(shape.intersection(box(x-.024,b,x+.024,t)))
    for ratio in ([.7] if low else [.29,.65,.87]):
        z=b+(t-b)*ratio;bars.append(shape.intersection(box(l,z-.024,r,z+.024)))
    face.prism(unary_union(bars),-.203,-.141,'iron window grid','steel sash')
    face.box((l+r)/2,b-.074,r-l+.19,.125,.27,.051,'stone sill','drip sill')
    ring=shape.buffer(.105,join_style='mitre').difference(shape)
    face.prism(ring,-.012,.041,'rust decoration','brick window edging')
    if arched:
        cap=shape.buffer(.24,join_style='mitre').difference(shape.buffer(.115,join_style='mitre')).intersection(box(l-.28,t-.53,r+.28,t+.30))
        face.prism(cap,-.008,.074,'pale carved lintel','arch hood')

def end_face(f,outer_on_left,low):
    """Each 14-metre wing has a projecting gabled bay and an inner parapet bay."""
    w=f.length;left=-w/2;right=w/2
    sign=-1 if outer_on_left else 1
    outer=sign*w*.24;inner=-sign*w*.265
    crown=Polygon([(outer-3.42,EAVE-.04),(outer+3.42,EAVE-.04),(outer,PEAK)])
    wall=unary_union([box(left,.04,right,EAVE),crown])
    units=[];ground=[]
    for x in (outer,inner):
        ground.append(opening(x,.89,2.59,2.06))
        for floor,z in enumerate([4.04,7.46,10.89]):
            patch=opening(x,z,2.16 if floor==2 else 2.37,2.12,arch=.55 if floor==2 and x==outer else 0)
            units.append((patch,floor==2 and x==outer))
    tiny=opening(outer,14.17,.54,.57,.23);units.append((tiny,True))
    visible=wall.difference(unary_union([*ground,*(v[0] for v in units)]))
    podium=visible.intersection(box(left,0,right,3.51));upper=visible.difference(podium)
    f.prism(upper,-.30,0,'warm pebble render','render and gabled face')
    f.prism(podium,-.30,0,'claret face brick','ground floor brick')
    f.box(0,.291,w,.56,.35,.005,'grey street plinth','street stone base')
    for s in ground:steel(f,s,low)
    for s,arched in units:steel(f,s,low,arched)
    for x in (outer,inner):
        for level in [3.51,6.50,9.91]:
            for dx in [-.78,0,.78]:
                f.box(x+dx,level+.52,.28,1.01,.058,.024,'rust decoration','triplet spandrel stripes')
    for e in [left+.12,right-.12]:
        inside=1 if e<0 else -1
        pieces=[]
        for i in range(39):
            width=.58 if i%2 else .95;z=3.36+i*.259
            pieces.append(box(e-.12 if inside==1 else e-width+.12,z,e+width-.12 if inside==1 else e+.12,z+.139))
        f.prism(unary_union(pieces),0,.053,'rust decoration','stepped quoins')
    for z in (3.43,13.59):f.box(0,z,w,.12,.19,.045,'shadow red brick','continuous brick string')
    gable_edges=[(outer-3.64,EAVE-.01),(outer,PEAK+.19),(outer+3.64,EAVE-.01)]
    ribbon=Polygon([*gable_edges,*[(x,z-.19)for x,z in reversed(gable_edges)]])
    f.prism(ribbon,-.48,.38,'dark weathered wood','gable verge')
    if not low:
        joint=[]
        for j in range(18):
            z=.64+j*.149
            for k in range(int(w/.37)+1):
                if (k*17+j*3)%7 in (1,3):
                    x=left+k*.37+(.185 if j%2 else 0)
                    q=box(x,z,x+.336,z+.117).intersection(podium)
                    if q.area>.006:joint.append(q)
        f.prism(unary_union(joint),.001,.016,'sienna headers','visible face brick bond')

def returns(f,low,label):
    w=f.length;cols=3 if w>8 else 2;openings=[]
    for i in range(cols):
        u=-w/2+w*(i+.5)/cols
        for z in [1.08,4.16,7.58,10.94]:
            openings.append(opening(u,z,min(1.30,w/cols*.43),1.79))
    shell=box(-w/2,.06,w/2,EAVE-.06).difference(unary_union(openings))
    f.prism(shell,-.25,0,'warm pebble render',label)
    f.prism(shell.intersection(box(-w/2,.06,w/2,3.42)),0,.024,'claret face brick','street level brick return')
    for s in openings:steel(f,s,low)
    f.box(0,EAVE-.14,w+.04,.19,.38,.055,'dark weathered wood','shaded eave plate')
    if not low:
        for i in range(max(2,round(w/.62))):
            u=-w/2+w*(i+.5)/round(w/.62)
            f.box(u,EAVE-.28,.085,.22,.43,.12,'dark weathered wood','exposed rafter tail')

def roof_panel(b,x0,x1,y0,y1,z0,z1,label,low):
    """Slope along X, ridge parallel to the depth of the street wing."""
    def pt(x,y,drop=0):return (x,y,z0+(x-x0)/(x1-x0)*(z1-z0)+drop)
    outer=[pt(x0,y0),pt(x1,y0),pt(x1,y1),pt(x0,y1)]
    verts=outer+[tuple(np.array(v)-[0,0,.095]) for v in outer]
    b.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'tile terracotta',label+'/tile slope')
    vertices=[];faces=[]
    for i in range(0,math.ceil((x1-x0)/(.58 if low else .29))):
        x=x0+i*(.58 if low else .29)
        if x+.023>=x1:continue
        j=len(vertices);vertices.extend([pt(x,y0,.010),pt(x+.034,y0,.015),pt(x+.034,y1,.015),pt(x,y1,.010)])
        faces.append((j,j+1,j+2,j+3))
    b.add(vertices,faces,'burnt clay',label+'/headlap courses')
    if not low:
        for i in range(1,math.ceil((y1-y0)/.225)):
            y=y0+i*.225
            verts=[pt(x0,y-.022,.014),pt(x0,y,.042),pt(x0,y+.021,.014),pt(x1,y-.022,.014),pt(x1,y,.042),pt(x1,y+.021,.014)]
            b.add(verts,[(0,3,4,1),(1,4,5,2)],'tile terracotta',label+'/tile rolls')

def chimney(b,x,y,base,low):
    b.box((x,y,base+1.10),(1.34,.81,2.20),'warm pebble render',label='Chimneys/stack')
    b.box((x,y,base+2.17),(1.48,.98,.18),'claret face brick',label='Chimneys/capping')
    for xx in (x-.43,x,x+.43):
        vert=[];faces=[];n=7 if low else 12
        for h,r in [(0,.145),(.54,.129),(.57,.163),(.64,.156),(.64,.093),(.32,.090)]:
            for j in range(n):
                t=j*math.tau/n;vert.append((xx+r*math.cos(t),y+r*math.sin(t),base+2.24+h))
        for k in range(5):
            for j in range(n):
                m=(j+1)%n;faces.append((k*n+j,k*n+m,(k+1)*n+m,(k+1)*n+j))
        b.add(vert,faces,'chimney pot','Chimneys/hollow terra cotta pots')
        b.add(vert,[tuple(range(5*n,6*n))],'flue opening','Chimneys/shaded flue')

def assemble(b,low=False):
    ends=[Facade(b,FRONT[0],FRONT[1],'East wing'),Facade(b,FRONT[4],FRONT[5],'West wing')]
    for i,f in enumerate(ends):
        end_face(f,i==0,low)
        xmin=min(f.a[0],f.b[0])
        xmax=xmin+f.length;gable=xmin+f.length*(.26 if i==0 else .74)
        center2=xmin+f.length*(.755 if i==0 else .245)
        lo=gable-3.53;hi=gable+3.53;label=['East roof','West roof'][i]
        roof_panel(b,lo,gable,-.38,DEPTH,EAVE+.02,PEAK+.12,label,low)
        roof_panel(b,gable,hi,-.38,DEPTH,PEAK+.12,EAVE+.02,label,low)
        lo2=xmin-.26 if i==1 else hi;hi2=xmax+.26 if i==0 else lo
        # The projecting inner bays have an unbroken dark eave across the front.
        roof_panel(b,lo2,center2,1.85,DEPTH,EAVE+.04,EAVE+1.09,label+'/inner',low)
        roof_panel(b,center2,hi2,1.85,DEPTH,EAVE+1.09,EAVE+.04,label+'/inner',low)
        apron=[(lo2,-.40,EAVE+.04),(hi2,-.40,EAVE+.04),(hi2,1.85,EAVE+.04),(center2,1.85,EAVE+1.09),(lo2,1.85,EAVE+.04)]
        b.add(apron,[(0,1,3),(1,2,3),(3,4,0)],'tile terracotta',label+'/hipped apron')
        for edge in range(11):
            u=(edge+.5)/11
            a=np.array(apron[0])*(1-u)+np.array(apron[1])*u
            c=a*.20+np.array(apron[3])*.80
            off=np.array([.025,0,.012]);b.add([a+off,a-off,c-off,c+off],[(0,1,2,3)],'burnt clay',label+'/hip tile joints')
        cornice=Facade(b,[lo2,-.03],[hi2,-.03],label+'/front')
        cornice.box(0,EAVE-.05,cornice.length,.21,.49,.13,'dark weathered wood','eave fascia')
        for j in range(13):
            cornice.box(cornice.length*((j+.5)/13-.5),EAVE-.21,.096,.22,.62,.14,'dark weathered wood','rafter tail')
        chimney(b,center2,6.83 if i==0 else 8.05,EAVE+.8,low)
    for k,name in [(1,'Court east'),(2,'Court south'),(3,'Court west')]:
        f=Facade(b,FRONT[k],FRONT[k+1],name);returns(f,low,'masonry recess')
    for i,(a,c) in enumerate([(FRONT[5],[18.69,DEPTH]),([-19.216,DEPTH],FRONT[0])]):
        returns(Facade(b,a,c,'Outer '+str(i+1)),low,'lateral masonry')
    f=Facade(b,FRONT[2],FRONT[3],'Court bay')
    outline=[f.point(x,0,z)[:2]for x,z in [(-2.10,.04),(-1.44,1.44),(1.44,1.44),(2.10,.04)]]
    for i,(a,c) in enumerate(zip(outline,outline[1:])):returns(Facade(b,a,c,'Bay '+str(i+1)),low,'splayed oriel')
    roof=[(*tuple(p),EAVE+.04)for p in outline];cx,cy=f.point(0,EAVE,.02)[:2]
    b.add([*roof,(cx,cy,EAVE+1.77)],[(0,1,4),(1,2,4),(2,3,4)],'burnt clay','Court bay/hipped tile cap')
    b.plan_prism(Polygon(P['strip_xy']),.04,.14,'grey street plinth','Section/bound footprint')
    b.box((-.12,12.86,EAVE-.01),(10.25,2.66,.21),'tile terracotta',label='Court/short roof')
    f=Facade(b,[18.69,DEPTH],[-19.216,DEPTH],'Section')
    f.prism(box(-f.length/2,.1,f.length/2,EAVE-.08),-.14,.0,'warm pebble render','approximate rear closure')
    # Independent gateway east of this entire building is outside this model.
    gate=Facade(b,FRONT[1],FRONT[4],'Court wall')
    gap=.83
    groundwall=box(-gate.length/2,.06,gate.length/2,2.72).difference(box(2.15,.06,2.15+gap,2.72))
    gate.prism(groundwall,-.26,.0,'warm pebble render','forecourt wall')
    gate.prism(groundwall.intersection(box(-gate.length/2,.04,gate.length/2,.32)),0,.041,'grey street plinth','grey skirting')
    gate.prism(groundwall.intersection(box(-gate.length/2,2.61,gate.length/2,2.76)),0,.074,'stone sill','wall coping')
    for side in [-1,1]:
        gate.box(2.57+side*.53,1.55,.24,3.04,.54,-.01,'grey street plinth','side piers')
    if any(len(part['label'].encode())>=60 for part in b.parts):raise ValueError('Editable group label too long')

if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
