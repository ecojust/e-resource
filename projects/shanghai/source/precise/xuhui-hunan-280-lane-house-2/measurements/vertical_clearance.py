"""Clip every mesh triangle against a convex ordinary footprint, retaining vertex height."""
import argparse
import json
from pathlib import Path

import numpy as np
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from project_house import read_mesh, digest


def grade(mesh,site):
    full=json.loads(site.read_bytes())
    results=[]
    for row in full['retained_city_features']:
        if row['overlap_m2']<=0:continue
        poly=orient(shape(row['footprint_local']),sign=1.)
        assert poly.symmetric_difference(poly.convex_hull).area<1e-7
        edges=np.asarray(poly.exterior.coords)
        xmin,ymin,xmax,ymax=poly.bounds
        hits={}
        for material,tri in read_mesh(mesh):
            for t in tri[(tri[:,:,0].min(1)<=xmax)&(tri[:,:,0].max(1)>=xmin)&(tri[:,:,1].min(1)<=ymax)&(tri[:,:,1].max(1)>=ymin)]:
                vertices=t
                for a,b in zip(edges,edges[1:]):
                    delta=b-a
                    signed=(vertices[:,1]-a[1])*delta[0]-(vertices[:,0]-a[0])*delta[1]
                    clipped=[]
                    for i,p in enumerate(vertices):
                        before=signed[i-1];after=signed[i]
                        if before*after<0:
                            q=vertices[i-1];clipped.append(q+(p-q)*before/(before-after))
                        if after>=0:clipped.append(p)
                    if not clipped:vertices=[];break
                    vertices=np.array(clipped)
                if len(vertices):
                    hits.setdefault(material,[]).extend(np.asarray(vertices).tolist())
        details={}
        for mat,hit in hits.items():
            points=np.array(hit);imin=points[:,2].argmin()
            details[mat]={'at_minimum_xyz':points[imin].tolist(),'height_range':[float(points[:,2].min()),float(points[:,2].max())]}
        zmin=min(v['height_range'][0]for v in details.values())
        results.append({'feature_id':row['id'],'ordinary_height':row['ordinary_height_m'],'overlap_m2':row['overlap_m2'],'min_overlapping_triangle_height':zmin,'clearance_m':zmin-row['ordinary_height_m'],'material_heights':details})
    return {'mesh_sha256':digest(mesh),'method':'Clip every authoring triangle, including exactly upright faces, by the half-planes of the convex ordinary polygon in XY; carry Z at every clipped edge. Test the actual minimum compared with the published ordinary extrusion height.','results':results}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['mesh','site','output']:p.add_argument(n,type=Path)
    args=p.parse_args();args.output.write_text(json.dumps(grade(args.mesh,args.site),indent=2)+'\n')
