"""Narrow closed clipping of Huaihai stone tips at the shared NE end plane."""
import math
import numpy as np
from shapely.geometry import LineString
from shapely.ops import polygonize,unary_union
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient

def clip_stone_tips(builder,front_end,next_end,clearance=.002,max_cut=.16):
    origin=np.asarray(front_end,float);t=np.asarray(next_end,float)-origin;t/=np.linalg.norm(t)
    outward=np.array([t[1],-t[0],0.]);t3=np.r_[t,0.];o3=np.r_[origin,0.]
    changed=[]
    selected={'huaihai/third-storey/continuous-stone-balustrade/deck',
              'huaihai/eighth-storey/continuous-metal-balcony/deck',
              'stone-base/large-scroll-corbel-15/scroll-body'}
    for part in builder.parts:
        if part['material']!='carved pale stone' or part['label'] not in selected:
            continue
        old_triangle_count=len(part['triangles'])
        old=np.asarray(part['vertices'],float)
        signed=(old-o3)@outward+clearance
        if signed.max()<=1e-9:continue
        # Strictly bounded local operation: never trim a remote building face.
        outside=old[signed>1e-9]
        if np.max(np.linalg.norm(outside[:,:2]-origin,axis=1))>1.6:
            raise ValueError('Shared-end clip unexpectedly reached beyond local ornament tip')
        if signed.max()>max_cut:
            raise ValueError('Shared-end clip exceeds stated local correction bound')
        verts=[];triangles=[];lookup={};sections=[]
        def index(v):
            key=tuple(round(float(x),9) for x in v)
            if key not in lookup:lookup[key]=len(verts);verts.append(tuple(float(x) for x in v))
            return lookup[key]
        def signed_at(v):return float(np.dot(v-o3,outward)+clearance)
        for tri in part['triangles']:
            original=[old[k] for k in tri];clipped=[];crossings=[]
            for a,b in zip(original,original[1:]+original[:1]):
                sa,sb=signed_at(a),signed_at(b);ina,inb=sa<=0,sb<=0
                if ina:clipped.append(a)
                if ina!=inb:
                    p=a+(b-a)*(sa/(sa-sb))
                    u,z=round(float(np.dot(p-o3,t3)),8),round(float(p[2]),8)
                    p=o3+t3*u-outward*clearance+np.array([0,0,z])
                    clipped.append(p);crossings.append(p)
            if len(clipped)>=3:
                ids=[index(v) for v in clipped]
                for k in range(1,len(ids)-1):triangles.append((ids[0],ids[k],ids[k+1]))
            if len(crossings)==2 and np.linalg.norm(crossings[0]-crossings[1])>1e-9:
                uv=[(round(float(np.dot(p-o3,t3)),8),round(float(p[2]),8)) for p in crossings]
                sections.append(LineString(uv))
        caps=list(polygonize(unary_union(sections)))
        if not caps:raise ValueError('No closed section found while clipping solid ornament')
        cap_count=0
        for cap in caps:
            for triangle in constrained_delaunay_triangles(cap).geoms:
                points=list(orient(triangle,sign=1).exterior.coords)[:3]
                ids=[index(o3+t3*u-outward*clearance+np.array([0,0,z])) for u,z in points]
                triangles.append(tuple(ids));cap_count+=1
        part['vertices']=verts;part['triangles']=triangles
        changed.append({'label':part['label'],'material':part['material'],
                        'old_triangles':old_triangle_count,
                        'new_triangles':len(triangles),'cap_triangles':cap_count,
                        'maximum_removed_normal_depth_m':float(signed.max()),
                        'removed_tip_bbox_enu':[outside.min(0).tolist(),outside.max(0).tolist()]})
    if {x['label'] for x in changed}!=selected:raise ValueError('Expected exactly the three reviewed stone parts')
    return {'method':'Closed plane clipping of only the three reviewed carved-pale-stone Huaihai ornament tips',
            'plane_source_edge':'frozen original vertex15→14; source body unchanged',
            'plane_origin_enu_xy':origin.tolist(),'plane_outward_normal_enu':outward.tolist(),
            'clearance_m':clearance,'maximum_allowed_cut_m':max_cut,'parts':changed,
            'maximum_actual_cut_m':max((x['maximum_removed_normal_depth_m'] for x in changed),default=0),
            'other_geometry_parts_edited':False}
