"""Editable geometry of the second-court tablet at Tuigeng Xiaozhu. Design axes X right, Y into wall, Z up."""
from pathlib import Path
import sys,json,hashlib,argparse,struct
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from shapely import set_precision, constrained_delaunay_triangles
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;S=HERE.parent
PROJECT=next((p for p in HERE.parents if (p/'source/precise/hongkou-general-post-office').is_dir()),None)
if PROJECT is None:
    import os
    PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path[:0]=[str(S/'measurements'),str(PROJECT/'source/precise/hongkou-general-post-office/source/common')]
from photo_architecture import Builder,pieces
from pediment_dimensions import data,plane,W,H
WALL='Lime plaster | buff-grey wall'
CAP='Cast stone | rounded arc moulding'
FIELD='Limestone | inscribed field'
FRET='Limestone | raised geometrical key'
SCRIPT='Limestone | positive running script'
BASE='Stone | drip and bed joints'
BACK='Lime plaster | unmeasured cut back'
names=[WALL,CAP,FIELD,FRET,SCRIPT,BASE,BACK]
def palette():
    rng=np.random.default_rng(628)
    tones={WALL:(178,169,151),CAP:(196,186,168),FIELD:(186,178,163),FRET:(194,186,170),SCRIPT:(193,184,169),BASE:(166,154,135),BACK:(168,160,145)}
    mats={}
    for n,rgb in tones.items():
        tex='lime-aggregate.jpg' if n in (WALL,BACK)else 'cut-stone-grain.jpg'
        p=HERE/tex
        if not p.is_file():
            fine=rng.normal(0,3.4 if n==WALL else 2.7,(128,128));large=rng.normal(0,2.5,(12,12))
            coarse=np.asarray(Image.fromarray(np.uint8(np.clip(150+large*8,0,255))).resize((128,128),Image.Resampling.BICUBIC),float)/8-18.75
            pix=np.uint8(np.clip((217+fine+coarse)[...,None]*np.array([1,.997,.985]),0,255));Image.fromarray(pix).save(p,quality=91)
        def lin(x):v=x/217;return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
        mats[n]=dict(color=[lin(v) for v in rgb],roughness=.89,texture=str(p))
    return mats

def solid(b,p,y_front,y_back,mat,label):
    p=set_precision(p,.0002).simplify(.0001,preserve_topology=True)
    b.prism(p,-y_back,-y_front,lambda x,z,d:(x,-d,z),mat,label)
def façade_polygon(b,pts,y_front,y_back,mat,name):
    solid(b,Polygon(pts),y_front,y_back,mat,name)
def profile_shell(b,rows,mat,label):
    """Closed solid spanning ordered cross-section loops along an arc or a straight rail."""
    a=np.stack(rows,axis=1);m,n=a.shape[:2];faces=[]
    for i in range(m-1):
        for j in range(n):faces.append((i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n))
    # The end loop is concave at the two beads. Respect all boundary edges and
    # wind the two caps opposite to their shared edges on the swept faces.
    for index,reverse in [(0,False),(m-1,True)]:
        yz=[tuple(point[1:]) for point in a[index]]
        polygon=Polygon(yz)
        assert polygon.is_valid and polygon.area>0
        ids={point:index*n+j for j,point in enumerate(yz)}
        for triangle in constrained_delaunay_triangles(polygon).geoms:
            points=list(triangle.exterior.coords)[:3]
            same_direction=triangle.exterior.is_ccw==polygon.exterior.is_ccw
            if same_direction==reverse:
                points.reverse()
            faces.append(tuple(ids[v] for v in points))
    # Select outward winding independently of sweep direction.
    verts=a.reshape(-1,3);vol=sum(np.dot(verts[f[0]],np.cross(verts[f[j]],verts[f[j+1]]))for f in faces for j in range(1,len(f)-1))
    b.add(verts,faces if vol>0 else [f[::-1]for f in faces],mat,label)
def line_ribbon(b,coords,width,y_front,y_back,mat,label):
    solid(b,LineString(coords).buffer(width/2,cap_style='flat',join_style='mitre'),y_front,y_back,mat,label)
def metric_row(uv,depth):
    chart=plane(uv,depth);return np.column_stack((chart[:,0],np.full(len(uv),depth),chart[:,1]))

# The two photograph edges bracket the moulding in the clear central run. At the left, the adjoining wall cuts across the arch.
edge_x=[175,200,240,280,320,360,400,440,480,520,560,600,640,680,715,746]
top=[210,194,179,166,157,151,149,149,154,162,172,186,203,225,248,274]
lower=[263,253,234,221,211,205,202,203,207,216,228,246,269,294,317,341]
def arc_geometry(b,lod):
    px=np.linspace(edge_x[0],edge_x[-1],31 if lod else 79)
    a=PchipInterpolator(edge_x,top)(px);z=PchipInterpolator(edge_x,lower)(px)
    def row(t,y):return metric_row(np.c_[px,a+(z-a)*t],y)
    # Wall face beneath curved fascia. Its back ends at the exhibition cut.
    edge=row(.44,.048);bottom=plane([[158,433],[879,405]],.048)
    left,right=edge[0,0],edge[-1,0];base_level=-.212
    shape=list(zip(edge[:,0],edge[:,2]));shape.extend([(right+.58,edge[-1,2]),(right+.58,base_level),(left,base_level)])
    façade_polygon(b,shape,.048,.28,WALL,'Court wall | visible weathered field')
    # Rounded crest, scotia and lower bead have independent depths and exposed sections.
    section=[(0,.15),(.0,.095),(.04,.004),(.11,-.057),(.18,-.087),(.242,-.086),(.27,-.074),(.285,-.041),(.325,-.040),(.35,-.074),(.389,-.099),(.46,-.106),(.55,-.102),(.63,-.080),(.71,-.046),(.77,-.034),(.81,-.052),(.852,-.064),(.895,-.060),(.937,-.040),(.978,-.011),(1,.04),(1,.068),(.84,.15)]
    if lod:section=[section[i] for i in (0,2,4,6,7,8,10,12,14,16,17,19,21,23)]
    profile_shell(b,[row(t,y)for t,y in section],CAP,'Segmental crest | bullnose, hollow and lower bead')
    shoulder=row(.25,.048)[-1];s0=right-.03;s1=right+.58
    def straight(points,name):
        profile_shell(b,[np.array([[s0,y,h],[s1,y,h+(s1-s0)*.003]])for y,h in points],CAP,name)
    sh=shoulder[2]+.033
    straight([(.14,sh+.02),(.012,sh+.02),(-.069,sh),(-.075,sh-.022),(-.058,sh-.043),(-.025,sh-.053),(-.019,sh-.079),(.038,sh-.093),(.14,sh-.093)],'Right return | stepped horizontal cap')
    s0=left;s1=right+.58;h=-.091
    straight([(.10,h+.040),(-.012,h+.040),(-.070,h+.022),(-.082,h+.002),(-.080,h-.025),(-.026,h-.043),(.047,h-.071),(.10,h-.071)],'Lower drip | projected band under inscription')
def tablet(b):
    w=W/2;f=box(-w,0,w,H);solid(b,f,-.0005,.048,FIELD,'Tablet | flat writing face')
    outer=box(-1.095,-.135,1.095,.614)
    ring=outer.difference(f)
    solid(b,ring,-.011,.046,FIELD,'Square border | bed for the carved key')
    def trim(half,bt,tp,width,depth,label):
        p=box(-half,bt,half,tp);solid(b,p.difference(p.buffer(-width,join_style='mitre')),depth,.002,FRET,label)
    trim(.917,-.017,.425,.012,-.021,'Tablet | fine inner raised rule')
    trim(1.085,-.131,.610,.018,-.024,'Frame | outer square mitres')
    # The two alternating three-turn returns can be followed independently. The rectified middle repeats every 55 / 261 pixels per metre.
    sp=.2107
    def keys(n,transform,label,clip):
        for i in range(n):
            a=i*sp
            strands=[[(a,.005),(a+.099,.005),(a+.099,.069),(a+.046,.069)],[(a+.007,.129),(a+.135,.129),(a+.135,.064),(a+.198,.064)]]
            for j,coords in enumerate(strands):
                path=LineString([transform(x,z)for x,z in coords]).buffer(.012,cap_style='flat',join_style='mitre').intersection(clip)
                if not path.is_empty:solid(b,path,-.031,-.009,FRET,f'{label} | repeat {i+1} return {j+1}')
    keys(11,lambda x,z:(-1.105+x,.445+z),'Top fret',box(-1.063,.430,1.065,.594))
    for sign in [-1,1]:
        keys(4,lambda x,z:(sign*(.927+z),.612-x),'Side fret '+str(sign),box(-1.073 if sign<0 else .920,-.109,-.920 if sign<0 else 1.073,.588))
    keys(11,lambda x,z:(-1.105+x,-.035-z),'Bottom fret',box(-1.063,-.116,1.063,-.025))
def stroke_poly(raw,offset,lod):
    arr=np.array(raw,float);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(arr[:,:2],axis=0),axis=1))]
    t=np.linspace(0,s[-1],max(len(s),int(s[-1]/(2.6 if lod else .9))))
    # Side-lit relief has its strongest dark return just below each crest.
    # On 2018 source pixels, the median negative edge is centred on the
    # initial hand trace. The opposite highlight is 3–4 pixels away.
    xy=PchipInterpolator(s,arr[:,:2],axis=0)(t)+offset-np.array([.64,1.40])
    r=PchipInterpolator(s,arr[:,2])(t)*1.12+.31
    shapes=[]
    for pt,rad in zip(xy,r):shapes.append(Point(*pt).buffer(rad,quad_segs=2 if lod else 4))
    return unary_union([unary_union((a,b)).convex_hull for a,b in zip(shapes,shapes[1:])])
def writing(b,lod):
    for glyph in data['letters']:
        parts=unary_union([stroke_poly(raw,np.array(glyph['offset']),lod)for raw in glyph['strokes']])
        for index,p in enumerate(pieces(parts)):
            # The measured contour is on the forward face of each positive stroke.
            def conv(r):return plane(np.asarray(r.coords),-.010)
            face=Polygon(conv(p.exterior),[conv(h)for h in p.interiors]).simplify(.0009 if lod else .00038,preserve_topology=True)
            label='Inscription | '+glyph['reading']+' | contact '+str(index+1)
            solid(b,face,-.0098,.0005,SCRIPT,label)
            if not lod:
                plateau=face.buffer(-.00065)
                if not plateau.is_empty:solid(b,plateau,-.0112,-.0096,SCRIPT,label+' eased crest')
def uv(part):
    # Keep UV areas on mitres and letter flanks. Material noise is generated from mathematical fields.
    v=np.asarray(part['vertices']);out=[];tri=[];tex=[]
    bounds=v.min(0);span=np.maximum(np.ptp(v,axis=0),.20)
    for face in part['triangles']:
        p=v[list(face)];normal=np.abs(np.cross(p[1]-p[0],p[2]-p[0]))
        axes=((1,2),(0,2),(0,1))[np.argmax(normal)];n=len(out);out.extend(p);tri.append((n,n+1,n+2))
        t=.015+.97*(p[:,axes]-bounds[list(axes)])/span[list(axes)];tex.extend((u,1-w)for u,w in t)
    part.update(vertices=out,triangles=tri,texcoords=tex)
META = dict(
    id='jingan-tuigeng-xiaozhu-inscribed-courtyard-pediment',
    name='退耕小筑二进院墙半弧题额与回纹框',
    heritage_group='5B049',
    viewer_page='tuigeng-xiaozhu-inscribed-courtyard-pediment.html',
    scope='独立展示长乐路662弄第二进院墙的题额、四字阳文与回纹。题面宽1.80米为比例假定。',
    photo_author='上海市文化旅游局提供资料，摄影者未单列；施泳峰报道并配独立远照。',
    photo_source='https://www.sohu.com/a/578713884_121106832',
    license_url='https://opensource.org/license/mit',
    geometry_license='MIT', texture_license='MIT', photos_embedded=False,
    attribution='照片来自2022年市文化旅游局长乐路图文。2023年施泳峰在《人民政协报》辨识第二进院墙与阳文题额。',
    copyright='Original architectural geometry, hand traces, and procedural finishes licensed under MIT. Historical and reference photographs remain with their rights holders.'
)
PALETTE = palette()

def add_building(builder, lod=False):
    start = len(builder.parts)
    arc_geometry(builder, lod)
    tablet(builder)
    writing(builder, lod)
    for part in builder.parts[start:]:
        uv(part)

def build(lod=False):
    builder = Builder(PALETTE)
    add_building(builder, lod)
    return builder
def write_named(path,builder):
    """Make the four words, border sections, cornice and wall independently selectable in standard glTF editors."""
    rights='原创建筑几何、手工描线和程序材质按 MIT 许可；外部参考照片版权归原权利人。模型中没有照片像素。'
    meta=dict(name='退耕小筑二进院墙半弧题额与回纹框',reading='退耕小筑',allDimensionsEstimated=True,originalPhotoPixelsEmbedded=False,copyright=rights)
    builder.save(path,meta)
    original=path.read_bytes();size=struct.unpack_from('<I',original,12)[0]
    doc=json.loads(original[20:20+size]);payload=original[20+size:]
    groups={}
    for prim in doc['meshes'][0]['primitives']:
        name=doc['materials'][prim['material']]['name']
        ac=doc['accessors'][prim['indices']]
        offset=0
        for part in builder.parts:
            if part['material']!=name:continue
            label=part['label'];words=label.split(' | ')
            if words[0]=='Inscription':group='题字 · '+words[1]
            elif 'fret' in words[0].lower():group=words[0]
            elif words[0] in ('Square border','Frame','Tablet'):group='Tablet and frame'
            else:group=words[0]
            count=3*len(part['triangles']);start=ac.get('byteOffset',0)+offset*4
            ranges=groups.setdefault(group,[])
            if ranges and ranges[-1][0]==prim and ranges[-1][1]+ranges[-1][2]*4==start:
                ranges[-1][2]+=count
            else:ranges.append([prim,start,count])
            offset+=count
        assert offset==ac['count'] and ac['componentType']==5125
    nodes=[];meshes=[]
    for name,ranges in groups.items():
        items=[]
        for old,start,count in ranges:
            ac=dict(doc['accessors'][old['indices']]);ac.update(byteOffset=start,count=count);i=len(doc['accessors']);doc['accessors'].append(ac)
            items.append(dict(old,indices=i))
        nodes.append(dict(name=name,mesh=len(meshes)));meshes.append(dict(name=name,primitives=items))
    doc['nodes']=nodes;doc['meshes']=meshes;doc['scenes'][0]['nodes']=list(range(len(nodes)))
    text=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();text+=b' '*((-len(text))%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(text)+len(payload))+struct.pack('<II',len(text),0x4e4f534a)+text+payload)
    aux=path.with_suffix('.geometry.json');audit=json.loads(aux.read_bytes());audit.update(editable_nodes=list(groups),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest());aux.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);a.add_argument('--lod',action='store_true');args=a.parse_args()
    b=build(args.lod);write_named(args.out,b)
    print(args.out.name,len(b.parts),sum(len(i['triangles'])for i in b.parts),hashlib.sha256(args.out.read_bytes()).hexdigest())
