"""Build the two open lotus emblems on the existing Bund 7 street piers."""
from copy import deepcopy
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient

HERE=Path(__file__).resolve().parent
TOOLS=HERE.parents[2]/'bund17/revisions/street-wing-doors'
sys.path.insert(0,str(TOOLS))
from build_wing_doors import Parts,chunks,glb

FACE='Bund 7 satin-gilt lotus'
EDGE='Bund 7 shaded bronze returns'
MATERIALS={FACE:([.72,.414,.095,1],.64,.33),EDGE:([.335,.178,.046,1],.65,.40)}

def path_points(start,segments,steps):
    """Sample cubic outlines in the observed width-height plane."""
    p=np.array(start);result=[p]
    for c1,c2,end in segments:
        c1,c2,end=map(np.array,(c1,c2,end))
        for t in np.linspace(0,1,steps+1)[1:]:
            result.append((1-t)**3*p+3*(1-t)**2*t*c1+3*(1-t)*t*t*c2+t**3*end)
        p=end
    return np.array(result)

def outline(width,height,lod):
    n=3 if lod else 7
    # The central diamond and the two inward-curled lower leaves are separate through-openings.
    side=path_points((0,1),[
        ((.085,.91),(.29,.73),(.403,.615)),((.477,.531),(.501,.449),(.496,.366)),
        ((.490,.259),(.409,.205),(.323,.157)),((.20,.086),(.070,.032),(0,0))],n)
    diamond=path_points((0,.855),[
        ((.080,.788),(.215,.661),(.298,.568)),((.224,.476),(.078,.346),(0,.290))],n)
    leaf=path_points((.073,.095),[
        ((.095,.159),(.133,.236),(.213,.281)),((.284,.326),(.355,.387),(.404,.460)),
        ((.420,.372),(.393,.304),(.350,.265)),((.277,.202),(.140,.141),(.073,.095))],n)
    mirror=np.array([-1,1])
    closed=lambda a:np.vstack((a,a[-2:0:-1]*mirror))
    scale=np.array([width,height])
    shape=orient(Polygon(closed(side)*scale,[closed(diamond)*scale,leaf[:-1]*scale,leaf[:-1]*mirror*scale]),sign=1)
    assert shape.is_valid and len(shape.interiors)==3
    return shape

def embossed_plate(shape,lod):
    """Make front, bevel, back and all four boundary walls from one perforated outline."""
    p=Parts();back=.184;rim=.239;front=.254
    face=shape.buffer(-(.010 if lod else .013),join_style='mitre',mitre_limit=2.5)
    assert face.geom_type=='Polygon' and len(face.interiors)==3
    def cap(area,material,depth,flip=False):
        for tri in constrained_delaunay_triangles(area).geoms:
            ring=np.asarray(orient(tri,sign=1).exterior.coords[:3]);verts=[(x,y,depth(x,y))for x,y in ring]
            p.surface(material,verts,[(2,1,0)if flip else(0,1,2)])
    cap(face,FACE,lambda x,y:front)
    cap(shape.difference(face),FACE,lambda x,y:rim if shape.boundary.distance(Point(x,y))<1.e-7 else front)
    cap(shape,EDGE,lambda x,y:back,True)
    for ring in (shape.exterior,*shape.interiors):
        coords=list(ring.coords)
        for a,b in zip(coords,coords[1:]):
            p.quad(EDGE,(*a,back),(*b,back),(*b,rim),(*a,rim))
    # Two short concealed standoffs under the top joint and the lower stem reach the original masonry.
    h=shape.bounds[3]
    for z in (.947*h,.073*h):p.box(EDGE,0,z,.041,.039,-.010,.190)
    return p.data()

def instances(lod):
    v=json.loads((HERE/'geometry-input.json').read_bytes());o=np.array(v['facade_origin_east_north_m'])
    tangent=np.array(v['tangent_east_north']);normal=np.array(v['outward_east_north'])
    basis=np.array([[tangent[0],0,-tangent[1]],[0,1,0],[normal[0],0,-normal[1]]])
    form=embossed_plate(outline(v['width_m'],v['height_m'],lod),lod)
    for u,side in zip(v['origin_of_each_pier_u_m'],('south','north')):
        xy=o+u*tangent;shift=[xy[0],v['bottom_m'],-xy[1]]
        yield 'Bund07 | '+side+' street pier | open lotus',{label:((pos@basis+shift).astype('<f4'),(norm@basis).astype('<f4'),faces)for label,(pos,norm,faces)in form.items()}


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
                      'bytes':target.stat().st_size,'added_triangles':total,'new_editable_parts':2}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
