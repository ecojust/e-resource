"""Fit the photographed black-and-gold wing doors into Bund 17's existing street openings."""
from hashlib import sha256
from pathlib import Path
import argparse,json,math,struct
from copy import deepcopy
import numpy as np

HERE=Path(__file__).resolve().parent
MATERIALS={
    'Patinated black bronze':([.027,.023,.020,1],.49,.47),
    'Recessed black door field':([.012,.014,.013,1],.29,.59),
    'Warm gilt bronze':([.56,.336,.112,1],.73,.40),
    'Shadowed address numerals':([.066,.051,.035,1],.30,.60)
}
DARK,FIELD,GOLD,NUMBER=MATERIALS


def chunks(path):
    data=path.read_bytes()
    magic,version,length,text_size,kind=struct.unpack_from('<4s4I',data)
    assert (magic,version,length,kind)==(b'glTF',2,len(data),0x4e4f534a)
    doc=json.loads(data[20:20+text_size]);off=20+text_size
    bin_size,bin_kind=struct.unpack_from('<II',data,off)
    assert bin_kind==0x004e4942 and off+8+bin_size==length
    return doc,data[off+8:]


def glb(path,doc,bin_data):
    text=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    text+=b' '*(-len(text)%4);bin_data+=b'\0'*(-len(bin_data)%4)
    header=struct.pack('<4s4I',b'glTF',2,28+len(text)+len(bin_data),len(text),0x4e4f534a)
    path.write_bytes(header+text+struct.pack('<II',len(bin_data),0x004e4942)+bin_data)


class Parts:
    def __init__(self):
        self.by_material={}

    def surface(self,mat,verts,faces):
        vertices,indices=self.by_material.setdefault(mat,([],[]))
        start=len(vertices);vertices.extend(verts)
        indices.extend(tuple(start+a for a in face)for face in faces)

    def quad(self,mat,a,b,c,d):
        self.surface(mat,[a,b,c,d],[(0,1,2),(0,2,3)])

    def box(self,mat,x,y,w,h,back,front):
        x0,x1=x-w/2,x+w/2;y0,y1=y-h/2,y+h/2
        assert w>0 and h>0 and front>back
        p=[(x0,y0,back),(x1,y0,back),(x1,y1,back),(x0,y1,back),
           (x0,y0,front),(x1,y0,front),(x1,y1,front),(x0,y1,front)]
        for ids in [(4,5,6,7),(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.quad(mat,*[p[i]for i in ids])

    def tube(self,mat,points,r,sides=8):
        points=np.asarray(points,float)
        if len(points)<2:return
        rings=[]
        for i,p in enumerate(points):
            tangent=points[min(i+1,len(points)-1)]-points[max(i-1,0)]
            tangent=tangent/np.linalg.norm(tangent)
            axis=np.array([0,0,1.]);perp=np.cross(tangent,axis);perp/=np.linalg.norm(perp)
            other=np.cross(tangent,perp)
            rings.append([p+r*(math.cos(j*math.tau/sides)*perp+math.sin(j*math.tau/sides)*other)for j in range(sides)])
        vertices=np.reshape(rings,(-1,3)).tolist();faces=[]
        for i in range(len(rings)-1):
            for j in range(sides):
                k=(j+1)%sides;a=i*sides
                faces.extend([(a+j,a+k,a+sides+k),(a+j,a+sides+k,a+sides+j)])
        end=(len(rings)-1)*sides
        faces.extend([(0,j+1,j)for j in range(1,sides-1)])
        faces.extend([(end,end+j,end+j+1)for j in range(1,sides-1)])
        self.surface(mat,vertices,faces)

    def disc(self,mat,x,y,rx,ry,back,front,sides=14):
        # Three elliptical rings give the medallions and leaf-like tips a rounded front.
        rings=[]
        for z,scale in [(back,.86),(front-.007,1),(front,.80)]:
            rings.extend((x+rx*scale*math.cos(i*math.tau/sides),y+ry*scale*math.sin(i*math.tau/sides),z)for i in range(sides))
        faces=[]
        for layer in range(2):
            for j in range(sides):
                a=layer*sides+j;b=layer*sides+(j+1)%sides
                faces.extend(((a,b,b+sides),(a,b+sides,a+sides)))
        for i in range(1,sides-1):faces.extend([(0,i+1,i),(2*sides,2*sides+i,2*sides+i+1)])
        self.surface(mat,rings,faces)

    def outline(self,mat,x0,x1,y0,y1,thickness,back,front):
        self.box(mat,(x0+x1)/2,y0,x1-x0,thickness,back,front)
        self.box(mat,(x0+x1)/2,y1,x1-x0,thickness,back,front)
        for x in [x0,x1]:
            self.box(mat,x,(y0+y1)/2,thickness,y1-y0-thickness,back,front)

    def data(self):
        result={}
        for label,(v,f)in self.by_material.items():
            points=np.asarray(v,dtype='<f4');faces=np.asarray(f,dtype='<u2')
            tri=points[faces].astype(float)
            areas=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
            assert np.linalg.norm(areas,axis=1).min()>1e-10,label
            normals=np.zeros_like(points,dtype=float)
            for j in range(3):np.add.at(normals,faces[:,j],areas)
            normals/=np.linalg.norm(normals,axis=1)[:,None];assert np.isfinite(normals).all()
            result[label]=(points,normals.astype('<f4'),faces)
        return result


def curved_points(fn,steps,z):
    return [(x,y,z) for x,y in (fn(i/(steps-1))for i in range(steps))]


def leaf(sgn,lod):
    p=Parts();cx=sgn*.500;p.box(FIELD,cx,1.412,.980,2.356,-.235,-.206)
    p.outline(DARK,cx-.453,cx+.453,.282,2.546,.046,-.213,-.139)
    p.outline(DARK,cx-.362,cx+.362,.452,2.325,.030,-.210,-.168)
    p.box(DARK,cx,.382,.812,.127,-.207,-.151)
    # Two bright strips meet at the centre joint; their top/bottom roundels
    # are visible in the unobscured northern door on the 2025 photograph.
    rail=sgn*.081;p.box(GOLD,rail,1.398,.071,1.990,-.185,-.143)
    for y in (.351,2.444):
        p.disc(GOLD,rail,y,.047,.061,-.186,-.126,10 if lod else 16)
    # Stepped dark meander corners framing the upper and lower leaf.
    for side in (-1,1):
        for yy,flip in ((.51,1),(2.28,-1)):
            d=.283*side
            path=[(cx+d,yy),(cx+d-.105*side,yy),(cx+d-.105*side,yy+.095*flip),
                  (cx+d-.035*side,yy+.095*flip),(cx+d-.035*side,yy+.195*flip)]
            p.tube(DARK,[(x,y,-.152)for x,y in path],.013,5 if lod else 8)
    # A swept garland runs between two raised tips. A medallion sits above the
    # centre and a narrow vertical pendant descends below the loop.
    for side in (-1,1):
        tip=cx+side*.138
        p.disc(GOLD,tip,2.075,.021,.045,-.194,-.115,8 if lod else 12)
        garland=curved_points(lambda t:(cx+side*.138*(1-t),2.055-.218*math.sin(t*math.pi/2)),7 if lod else 13,-.123)
        p.tube(GOLD,garland,.018,6 if lod else 10)
    p.disc(GOLD,cx,2.122,.037,.052,-.192,-.106,10 if lod else 16)
    p.disc(GOLD,cx,2.038,.032,.030,-.189,-.114,10 if lod else 16)
    p.tube(GOLD,[(cx,1.847,-.133),(cx,1.562,-.135),(cx,1.102,-.132)],.012,5 if lod else 8)
    p.disc(GOLD,cx,1.065,.025,.041,-.184,-.106,8 if lod else 12)
    p.tube(GOLD,[(cx,.994,-.130),(cx,.921,-.133)],.014,5 if lod else 8)
    p.disc(GOLD,cx,.903,.017,.025,-.182,-.116,8 if lod else 12)
    return p.data()


def head(lod):
    p=Parts()
    # The dark glazed cavity and old V4.4 substrate remain behind the facework.
    p.box(FIELD,0,2.981,1.98,.752,-.232,-.201)
    for x in (-1.038,1.038):p.box(DARK,x,1.810,.092,3.108,-.235,-.107)
    p.box(DARK,0,2.608,2.120,.124,-.228,-.108)
    p.box(GOLD,0,2.597,2.065,.035,-.114,-.081)
    p.box(GOLD,0,2.650,2.035,.018,-.126,-.094)
    p.box(DARK,0,3.369,2.119,.071,-.231,-.123)
    for side in (-1,1):
        scroll=curved_points(lambda t:(side*(.31+.603*t),2.701+.094*t+.052*math.sin(math.tau*t)),8 if lod else 16,-.162)
        p.tube(DARK,scroll,.027,6 if lod else 8)
        loop=curved_points(lambda t:(side*(.654+.119*math.cos(t*1.65*math.pi)),2.836+.117*math.sin(t*1.65*math.pi)),8 if lod else 16,-.163)
        p.tube(DARK,loop,.028,6 if lod else 8)
        p.disc(GOLD,side*.037,2.695,.029,.038,-.191,-.117)
    p.disc(GOLD,0,2.739,.039,.055,-.195,-.110)
    # Both dates show the number 17 on a light, narrow lintel over each door.
    # Its existing stone panel front is at d=.10. Use dark fitted numerals.
    for xy in [[(-.091,3.512),(-.050,3.546),(-.050,3.405)],
               [(.004,3.541),(.089,3.541),(.034,3.405)]]:
        p.tube(NUMBER,[(x,y+.080,.108)for x,y in xy],.011,5 if lod else 8)
    return p.data()


def instances(lod):
    s=json.loads((HERE/'news-footprint.json').read_bytes())
    a,b=np.asarray(s['polygon_local_east_north'])[2:4];mid=(a+b)/2
    t=(b-a)/np.linalg.norm(b-a);out=np.array([t[1],-t[0]])
    width=np.linalg.norm(b-a)/2-3.55/2
    basis=np.array([[t[0],0,-t[1]],[0,1,0],[out[0],0,-out[1]]])
    for side,location in [(-1,'south'),(1,'north')]:
        xy=mid+t*width*side;translation=[xy[0],0,-xy[1]]
        for name,data in [('left leaf',leaf(-1,lod)),('right leaf',leaf(1,lod)),('transom, jambs and number',head(lod))]:
            pieces={}
            for material,(pos,norm,faces)in data.items():
                # The archived wing openings contain generic pale mullions
                # in front of the earlier glazing. Seat the opaque door leaves
                # ahead of those bars, still behind the existing stone jambs.
                local=pos.copy()
                if material!=NUMBER:
                    local[:,2]+=.091
                pieces[material]=((local@basis+translation).astype('<f4'),(norm@basis).astype('<f4'),faces)
            yield f'Bund17 | {location} wing door | {name}',pieces


def augment(original,binary,lod):
    doc=deepcopy(original);blob=bytearray(binary)
    indices={}
    for label,(base,metal,rough)in MATERIALS.items():
        assert not any(m.get('name')==label for m in doc['materials'])
        indices[label]=len(doc['materials']);doc['materials'].append({'name':label,'pbrMetallicRoughness':
            {'baseColorFactor':base,'metallicFactor':metal,'roughnessFactor':rough}})
    def add_array(array,target,kind,component,bounds=False):
        blob.extend(b'\0'*(-len(blob)%4));v=len(doc['bufferViews']);payload=array.tobytes()
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':len(payload),'target':target});blob.extend(payload)
        acc={'bufferView':v,'componentType':component,'count':len(array),'type':kind}
        if bounds:acc.update(min=array.min(0).tolist(),max=array.max(0).tolist())
        doc['accessors'].append(acc);return len(doc['accessors'])-1
    count=0;scene=doc['scenes'][doc.get('scene',0)]
    for name,parts in instances(lod):
        primitives=[]
        for material,(points,normals,faces)in parts.items():
            pos=add_array(points,34962,'VEC3',5126,True);normal=add_array(normals,34962,'VEC3',5126)
            idx=add_array(faces.ravel(),34963,'SCALAR',5123)
            primitives.append({'attributes':{'POSITION':pos,'NORMAL':normal},'indices':idx,'material':indices[material]})
            count+=len(faces)
        n=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':primitives})
        scene['nodes'].append(len(doc['nodes']));doc['nodes'].append({'name':name,'mesh':n})
    doc['buffers'][0]['byteLength']=len(blob)
    return doc,bytes(blob),count


def main():
    parser=argparse.ArgumentParser();parser.add_argument('prior',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.mkdir(exist_ok=True,parents=True)
    reference=json.loads((HERE/'baseline.json').read_bytes())['assets'];result={}
    for role in ('raw','web','lod'):
        path=args.prior/reference[role]['file']
        assert sha256(path.read_bytes()).hexdigest()==reference[role]['sha256']
        doc,binary=chunks(path);new,b,total=augment(doc,binary,role=='lod')
        target=args.output/(role+'.glb');glb(target,new,b)
        result[role]={'original_sha256':reference[role]['sha256'],'sha256':sha256(target.read_bytes()).hexdigest(),
                      'bytes':target.stat().st_size,'added_triangles':total,'new_editable_parts':6}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
