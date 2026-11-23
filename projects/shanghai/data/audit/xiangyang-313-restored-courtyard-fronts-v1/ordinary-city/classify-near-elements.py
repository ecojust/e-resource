"""Measure original draw-element ownership for the one photographed source building."""
from pathlib import Path
import hashlib, json, math, struct
import argparse
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('decoded_near',type=Path);ap.add_argument('evidence_directory',type=Path);ap.add_argument('output',type=Path)
args=ap.parse_args()
W=args.evidence_directory
p=args.decoded_near
binary = p.read_bytes()
length, = struct.unpack_from('<I',binary,12)
scene = json.loads(binary[20:20+length])
data = memoryview(binary)[28+length:]
source = json.loads((W/'old-26-features.json').read_bytes())
baseline = json.loads((W/'public-baseline.json').read_bytes())
x0, y0 = source['origin']
r = 6378137.0 * math.cos(math.radians(y0))
y_offset = math.asinh(math.tan(math.radians(y0)))
def to_local(lon,lat):
    return r * math.radians(lon-x0), -r*(math.asinh(math.tan(math.radians(lat)))-y_offset)
polys = {}
for row in source['features']:
    geometry = row['geometry']
    polygons = geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
    polys[row['localId']] = [[[to_local(*point) for point in ring] for ring in polygon] for polygon in polygons]
def ring_relation(x,z,ring):
    inside=False
    distance=float('inf')
    for (ax,az),(bx,bz) in zip(ring,ring[1:]):
        u,v=bx-ax,bz-az
        if (az>z)!=(bz>z) and x<ax+(z-az)*u/v:inside=not inside
        t=min(1,max(0,((x-ax)*u+(z-az)*v)/(u*u+v*v))) if u or v else 0
        distance=min(distance,math.hypot(ax+t*u-x,az+t*v-z))
    return inside,distance
def distance(x,z,shapes):
    best=float('inf')
    for rings in shapes:
        checks=[ring_relation(x,z,ring)for ring in rings]
        if checks[0][0] and not any(v for v,_ in checks[1:]):return 0.
        best=min(best,*(d for _,d in checks))
    return best
target_id=3304
keys=[(v,w)for v,w in polys.items() if v!=target_id]
observed=[]
def classify(position):
    x,_,z=position
    d=distance(x,z,polys[target_id])
    if d>.6:return False
    nearest=min((distance(x,z,shapes),i)for i,shapes in keys)
    if nearest[0]<d-.01:return False
    assert nearest[0]-d>.01,('Ambiguous target',position,d,nearest)
    observed.append((d,nearest[0]-d))
    return True
def access(i):
    a=scene['accessors'][i];b=scene['bufferViews'][a['bufferView']]
    chars={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}
    lengths={'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}
    fmt=struct.Struct('<'+chars[a['componentType']]*lengths[a['type']])
    start=a.get('byteOffset',0)+b.get('byteOffset',0);stride=b.get('byteStride',fmt.size)
    return [fmt.unpack_from(data,start+v*stride)for v in range(a['count'])]
report=[]
total=0;visible=0
def summarize(kind,n,primitive,selected,each=1):
    global total,visible
    ids=[i for i,match in enumerate(selected) if match]
    other=[i for i,match in enumerate(selected) if not match]
    total+=each*len(selected);visible+=each*len(ids)
    report.append({'kind':kind,'node':n,'primitive':primitive,'total':len(selected),'target_element_ordinals':ids,'triangles_per_element':each,'retained_element_count':len(other),'retained_ordinals_u32le_sha256':hashlib.sha256(b''.join(struct.pack('<I',i) for i in other)).hexdigest()})
for n,node in enumerate(scene['nodes']):
    mesh=scene['meshes'][node['mesh']]
    if 'EXT_mesh_gpu_instancing' in node.get('extensions',{}):
        translation=access(node['extensions']['EXT_mesh_gpu_instancing']['attributes']['TRANSLATION'])
        each=sum(scene['accessors'][p['indices']]['count']//3 for p in mesh['primitives'])
        summarize('instance',n,None,[classify(p)for p in translation],each)
    else:
        for i,p in enumerate(mesh['primitives']):
            positions=access(p['attributes']['POSITION']);indices=access(p['indices'])
            triangles=[]
            for a in range(0,len(indices),3):
                pts=[positions[k] for k, in indices[a:a+3]]
                triangles.append(classify([sum(v)/3 for v in zip(*pts)]))
            summarize('triangle',n,i,triangles)
assert total==baseline['ordinary_near']['expandedTriangles']==72038 and 0<visible<total
out={'base':baseline['commit'],'source_key':baseline['feature_key'],'source_local_id':3304,
     'baseline_compressed_sha256':baseline['ordinary_near']['sha256'],'decoded_view_sha256':hashlib.sha256(binary).hexdigest(),
     'covered_near_ids':baseline['ordinary_near']['featureLocalIds'],'unchanged_local_ids':baseline['remain_near_local_ids'],
     'expanded_triangles':total,'target_expanded_triangles':visible,'retained_expanded_triangles':total-visible,
     'target_elements':len(observed),'max_target_distance_m':max(x for x,_ in observed),'min_target_lead_over_any_neighbor_m':min(y for _,y in observed),
     'method':'Instanced buildings use original translation centres. Continuous meshes use original triangle centroids. Only the target group needs a unique geometric owner. Record target ordinals and hash the complement in original order.','parts':report}
args.output.write_text(json.dumps(out,indent=2)+'\n')
print(total,visible,total-visible,len(observed),out['min_target_lead_over_any_neighbor_m'])
