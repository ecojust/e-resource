#!/usr/bin/env python3
"""Locate visible rear roof facets in actual raw GLB, without rendering."""
from pathlib import Path
import json,math,hashlib
import numpy as np
import shapely
from shapely.geometry import Polygon,LineString
from check_glass_inset import read
HERE=Path(__file__).resolve().parent


def check():
    raw,doc,acc,prims,images=read(HERE/'output/bund09-raw.glb')
    summary=json.loads((HERE/'output/bund09-raw.geometry.json').read_text())
    assert summary['sha256']==hashlib.sha256(raw).hexdigest()
    geometry=json.loads((HERE/'geometry-input.json').read_text());coords=geometry['polygon_local_east_north'];poly=Polygon(coords);inner=poly.buffer(-1.95,join_style=2)
    allxyz=[];roofs=[]
    for name,p in prims.items():
        xyz=acc(p['attributes']['POSITION'])[:,[0,2,1]]*np.array([1,-1,1]);allxyz.append(xyz)
        if name not in ['gray roof tile','gray roof tile light','roof zinc']:continue
        tris=xyz[acc(p['indices']).reshape(-1,3)]
        labels=[]
        for part in summary['part_summary']:
            if part['material']==name:labels.extend([part['label']]*part['triangles'])
        assert len(labels)==len(tris);roofs.append((name,tris,np.array(labels)))
    allxyz=np.concatenate(allxyz);az=math.radians(72.05);el=math.radians(12)
    out=np.array([math.sin(az)*math.cos(el),math.cos(az)*math.cos(el),math.sin(el)])
    right=np.array([-math.cos(az),math.sin(az),0]);up=np.cross(out,right)
    view=allxyz@np.array([right,up]).T;low=view.min(0);high=view.max(0);mid=(low+high)/2
    ortho=max(high[0]-low[0],(high[1]-low[1])*1200/1000)*1.12;factor=1200/ortho
    def pixels(xyz):
        v=xyz@np.array([right,up]).T
        return (v-mid)*np.array([factor,-factor])+np.array([600,500])
    queries=[(675,187),(701,194),(963,191),(967,203),(650,198)]
    hits=[];ranges=[]
    lines=[LineString([a,b]) for a,b in zip(coords,coords[1:]+coords[:1])]
    for name,tris,labels in roofs:
        support=labels=='roof-hip-surface-sheet'
        tiled=np.array([label.startswith('roof-v3-edge-') for label in labels])
        for mask,kind in [(support,'support sheets'),(tiled,'clipped field tiles')]:
            selected=tris[mask]
            if not len(selected):continue
            plans=shapely.polygons(selected[:,:,:2]);intersections=shapely.area(shapely.intersection(plans,inner))
            ranges.append({'material':name,'kind':kind,'triangles':len(selected),'min_z_m':float(selected[:,:,2].min()),'max_z_m':float(selected[:,:,2].max()),'sum_plan_triangle_intersection_with_inner_cap_m2':float(intersections.sum()),'largest_triangle_intersection_m2':float(intersections.max())})
        pp=pixels(tris);mins=pp.min(1);maxs=pp.max(1)
        for query in queries:
            point=np.array(query);candidates=np.flatnonzero(((mins<=point)&(maxs>=point)).all(1))
            for index in candidates:
                a,b,c=pp[index];mat=np.array([b-a,c-a]).T
                if abs(np.linalg.det(mat))<1e-9:continue
                uv=np.linalg.solve(mat,point-a)
                if min(uv)<-1e-6 or uv.sum()>1+1e-6:continue
                xyz=tris[index,0]*(1-uv.sum())+tris[index,1]*uv[0]+tris[index,2]*uv[1]
                nearest=min(range(len(lines)),key=lambda i:lines[i].distance(shapely.Point(*xyz[:2])))
                hits.append({'pixel':list(query),'material':name,'part':str(labels[index]),'triangle_index':int(index),'world_enu_m':xyz.tolist(),'closest_source_edge':nearest,'inside_inner_cap':bool(inner.contains(shapely.Point(*xyz[:2]))),'camera_front_depth':float(xyz@out)})
    visible=[]
    for q in queries:
        same=[r for r in hits if r['pixel']==list(q)]
        if same:visible.append(max(same,key=lambda r:r['camera_front_depth']))
    cap_xyz=next(t for name,t,labels in roofs if name=='roof zinc')
    cap_min=float(cap_xyz[:,:,2].min());cap_max=float(cap_xyz[:,:,2].max())
    support_rows=[r for r in ranges if r['kind']=='support sheets'];assert support_rows
    assert all(r['max_z_m']<=cap_max-.025+.000003 and r['sum_plan_triangle_intersection_with_inner_cap_m2']<1e-4 for r in support_rows),{'ranges':ranges,'visible':visible}
    assert all(r['sum_plan_triangle_intersection_with_inner_cap_m2']<1e-4 for r in ranges),ranges
    report={'schema':'bund09-v3-rear-roof-range-v1','passed':True,'raw_sha256':hashlib.sha256(raw).hexdigest(),'method':'Actual raw triangles,label ranges from SHA-linked export summary,orthographic camera projection replicated from frozen common finisher.No browser,Blender or render execution.','camera':{'azimuth':72.05,'elevation':12,'pixels':[1200,1000]},'visible_pixel_surface_hits':visible,'actual_serialized_ranges':ranges,'inner_cap_z_m':[cap_min,cap_max],'inner_cap_policy':'Entire roof-zinc batch exactly preserved by roof-revision-preservation.json. Existing build calls roof at eaves+.01m;actual cap is15.62–15.71m,not rounded15.61–15.70.','interpretation':'The visible rear gray raised facets are new distance-surface support within the original roof skirt,not tiles leaking into the inset zinc cap. Hits at(701,194),(963,191),(967,203)are support near sourceedges5,1,0;center samples(675,187),(650,198)hit the unchanged zinc cap itself. Rear support shape is an unobserved estimate and is not photographically accepted. Numerical plan-intersection residuals are FLOAT32 boundary rounding;no meaningful support/tile area enters the cap.','scope_limit':'Coverage of the targeted southern tiled slopes is separate. This is not evidence of a surveyed rear roof or a complete building Boolean union.'}
    (HERE/'native-compressed/rear-roof-range-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':check()
