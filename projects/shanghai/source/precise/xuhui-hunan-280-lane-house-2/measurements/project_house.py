"""Intersect exact authored triangles with retained city footprints in surveyed metre coordinates."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np
from shapely.geometry import shape, Polygon, Point, mapping, box
from shapely.ops import unary_union, transform

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def read_mesh(path):
    raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+length]);bin=memoryview(raw)[28+length:]
    def array(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        kind={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        count={'SCALAR':1,'VEC3':3}[a['type']];size=np.dtype(kind).itemsize
        return np.ndarray((a['count'],count),kind,buffer=bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',count*size),size))
    for node in doc['nodes']:
        assert set(node).issubset({'name','mesh'}), 'Unbaked parent/transform in this input'
        for p in doc['meshes'][node['mesh']]['primitives']:
            v=array(p['attributes']['POSITION']).astype(float)
            triangles=v[array(p['indices']).reshape(-1,3)]
            xyz=triangles[:,:,[0,2,1]]
            xyz[:,:,1]*=-1
            yield doc['materials'][p['material']]['name'],xyz

def tri_union(groups):
    batches=[];pending=[];count=0
    for material,triangles in groups:
        for t in triangles:
            d=t[1,:2]-t[0,:2];e=t[2,:2]-t[0,:2]
            if abs(d[0]*e[1]-d[1]*e[0])<1e-8:continue
            pending.append(Polygon(t[:,:2]));count+=1
            if len(pending)>=200:
                batches.append(unary_union(pending));pending.clear()
    if pending:batches.append(unary_union(pending))
    return unary_union(batches),count

def do(mesh,table,registration):
    survey=json.loads(registration.read_bytes());lon,lat=survey['origin_wgs'];a=math.radians(survey['x_azimuth_deg']);mx=111320*math.cos(math.radians(lat));my=110860.
    def local(lg,lt):
        e,n=(lg-lon)*mx,(lt-lat)*my;return math.sin(a)*e+math.cos(a)*n,-math.cos(a)*e+math.sin(a)*n
    def geographic(x,y,z=None):
        x=np.asarray(x);y=np.asarray(y)
        return (lon+(math.sin(a)*x-math.cos(a)*y)/mx,lat+(math.cos(a)*x+math.sin(a)*y)/my)
    complete=list(read_mesh(mesh))
    exact,n=tri_union(complete)
    simplified=exact.simplify(.015,preserve_topology=True)
    table_data=json.loads(gzip.decompress(table.read_bytes()))
    retained=[]
    for item in table_data['features']:
        g=shape(item['geometry'])
        if g.distance(Point(lon,lat))>.0009:continue
        q=transform(local,g)
        gap=exact.distance(q)
        if gap>24:continue
        hit=exact.intersection(q)
        row={'id':item['localId'],'key':item['key'],'ordinary_height_m':item['height'],
             'area_m2':q.area,'overlap_m2':hit.area,'gap_m':gap,'footprint_local':mapping(q)}
        if hit.area>0:
            z0,z1=item.get('base',0),item['height'];matches=[]
            for material,tris in complete:
                # Vertical clipping is exact at each flat triangle and conservative for sloping
                # triangles crossing the old roof. Compute the latter separately in 3D below.
                candidates=tris[(np.min(tris[:,:,2],axis=1)<=z1)&(np.max(tris[:,:,2],axis=1)>=z0)]
                for tri in candidates:
                    vert=list(tri)
                    for zedge,sgn in [(z0,1),(z1,-1)]:
                        out=[]
                        for i,p in enumerate(vert):
                            p0=vert[i-1];side=(p[2]-zedge)*sgn;oldside=(p0[2]-zedge)*sgn
                            if side*oldside<0:out.append(p0+(p-p0)*((zedge-p0[2])/(p[2]-p0[2])))
                            if side>=0:out.append(p)
                        vert=out
                        if not vert:break
                    if len(vert)<3:continue
                    uv=np.asarray(vert)[:,:2]
                    if uv[:,0].max()<q.bounds[0] or uv[:,0].min()>q.bounds[2] or uv[:,1].max()<q.bounds[1] or uv[:,1].min()>q.bounds[3]:continue
                    obj=Polygon(uv)
                    if obj.area<1e-10:continue
                    overlap=obj.intersection(q)
                    if overlap.area>1e-10:matches.append((material,overlap))
            clipped=unary_union([x for _,x in matches])
            row.update(vertically_clipped_intersection_m2=clipped.area,intersection_local=mapping(hit.simplify(.005,preserve_topology=True)),
                       volumetric_intersections_by_material_m2={m:unary_union([g for k,g in matches if k==m]).area for m in sorted({k for k,g in matches})},
                       witness_point_xy=list(clipped.representative_point().coords[0])if not clipped.is_empty else None)
        retained.append(row)
    retained.sort(key=lambda v:(v['gap_m'],-v['overlap_m2']))
    return {'source_mesh_sha256':digest(mesh),'ordinary_feature_table_sha256':digest(table),'registration_sha256':digest(registration),'origin_wgs84':survey['origin_wgs'],'x_azimuth_deg':survey['x_azimuth_deg'],
            'method':'All non-zero-area vertically projected authoring triangles are unioned (glTF x,-z). Exact polygon operations for intersections and distances. Each triangle is also clipped to the original extrusion vertical interval. Display footprints simplified to 0.015 m. Empty courtyards, wall interiors and spaces between walls remain empty.',
            'plan_area_actual_surfaces_m2':exact.area,'plan_bounds':exact.bounds,'plan_component_count':len(exact.geoms) if exact.geom_type=='MultiPolygon'else 1,
            'plan_positive_area_triangles':n,'projection_local_m':mapping(simplified),'projection_wgs84':mapping(transform(geographic,simplified)),
            'retained_city_features':retained}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ['mesh','table','registration','output']:cli.add_argument(name,type=Path)
    args=cli.parse_args();args.output.write_text(json.dumps(do(args.mesh,args.table,args.registration),separators=(',',':'))+'\n')
