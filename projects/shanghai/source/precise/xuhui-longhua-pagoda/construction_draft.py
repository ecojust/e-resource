#!/usr/bin/env python3
"""Longhua DESIGN-ONLY analytic helpers. No mesh/export/render capability.

Only --emit-plan writes a small JSON control plan. All true dimensions except
documented overall height remain caller-supplied or null. Source vertex order
and edge IDs are never rotated to fabricate a north-facing facade.
"""
from pathlib import Path
import argparse, hashlib, json, math

HERE=Path(__file__).resolve().parent
EARTH_R=6378137.0

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def enu(point,anchor):
    k=EARTH_R*math.pi/180
    return ((point[0]-anchor[0])*k*math.cos(math.radians(anchor[1])),
            (point[1]-anchor[1])*k)

def bearing(e,n):return math.degrees(math.atan2(e,n))%360

def signed_area(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))/2

def source_edges(source):
    ring=source['raw']['feature']['geometry']['coordinates'][0]
    anchor=source['source_shape']['centroid_lonlat']
    points=[enu(p,anchor) for p in ring[:-1]]
    assert len(points)==8 and ring[0]==ring[-1] and signed_area(points)<0
    result=[]
    for i,a in enumerate(points):
        b=points[(i+1)%8];de,dn=b[0]-a[0],b[1]-a[1];length=math.hypot(de,dn)
        # CW traversal: outward normal is on the left, not Facade's right.
        outward=(-dn/length,de/length)
        result.append({'edge_id':i,'source_vertex_ids':[i,(i+1)%8],
            'a_enu_m':list(a),'b_enu_m':list(b),'length_m':length,
            'source_tangent_bearing_deg':bearing(de,dn),
            'outward_bearing_deg':bearing(*outward),'outward_enu':list(outward),
            'future_Facade_endpoints':'reverse b,a for the audited CCW/right-outward Facade API'})
    return result

def scaled_source_ring(source,scale):
    """Analytic template only; scale is NOT a survey-derived wall/eave ratio."""
    if not 0<scale<=1:raise ValueError('Choose an explicit scale within the source envelope')
    anchor=source['source_shape']['centroid_lonlat']
    return [tuple(scale*x for x in enu(p,anchor)) for p in source['raw']['feature']['geometry']['coordinates'][0][:-1]]

def opening_kind(level,edge_id,*,first_level_open_parity):
    """Two unresolved parity scenarios remain; caller MUST specify one.

    Level is 1..7. Each has 4 through openings and4 blind niches. A45deg step
    changes parity, without rotating the footprint or independent columns.
    """
    if level not in range(1,8) or edge_id not in range(8) or first_level_open_parity not in (0,1):
        raise ValueError('Seven levels, eight stable edge IDs, explicit parity0/1 required')
    return 'through_cusped_door' if edge_id%2==(first_level_open_parity+level-1)%2 else 'blind_rectangular_niche'

def cubic(a,b,c,d,t):
    return tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in (0,1))

def cusped_opening_profile(width,height,segments_per_curve=8):
    """Schematic multi-lobed壸门 outline, not a traced measured photo contour.

    Future masonry subtracts this polygon; an opaque rectangle is not placed
    behind an intended opening. The two shoulder lobes and rounded central
    crest require original-resolution controls before final geometry.
    """
    if min(width,height)<=0 or segments_per_curve<4:raise ValueError('Invalid opening control')
    curves=[((-.5,.66),(-.5,.76),(-.37,.83),(-.28,.83)),
            ((-.28,.83),(-.25,.88),(-.23,.94),(-.14,.94)),
            ((-.14,.94),(-.08,1),(+.08,1),(+.14,.94)),
            ((+.14,.94),(+.23,.94),(+.25,.88),(+.28,.83)),
            ((+.28,.83),(+.37,.83),(+.5,.76),(+.5,.66))]
    points=[(-width/2,0),(width/2,0),(width/2,.66*height)]
    top=[]
    for controls in curves:
        for i in range(segments_per_curve):
            x,z=cubic(*controls,i/segments_per_curve);top.append((x*width,z*height))
    top.append((width/2,.66*height))
    points+=list(reversed(top[:-1]))
    return points

def roof_patch_point(inner_edge,outer_edge,s,t,*,inner_z,eave_mid_z,corner_lift,sag):
    """Continuous analytic curved eave surface; produces a single point only.

    s runs along a face, t runs outward. At shared octagonal corners the two
    neighboring patches use the same position and elevation. Future meshing
    must weld these shared boundaries, not extrude8closed overlapping boxes.
    """
    if not 0<=s<=1 or not 0<=t<=1 or min(corner_lift,sag)<0:
        raise ValueError('Invalid normalized roof controls')
    inside=tuple(inner_edge[0][j]*(1-s)+inner_edge[1][j]*s for j in (0,1))
    outside=tuple(outer_edge[0][j]*(1-s)+outer_edge[1][j]*s for j in (0,1))
    xy=tuple(inside[j]*(1-t)+outside[j]*t for j in (0,1))
    z=inner_z*(1-t)+eave_mid_z*t-sag*4*t*(1-t)+corner_lift*t*t*abs(2*s-1)**6
    return (*xy,z)

def tile_layer_offset(course,*,step_m,skin_thickness_m):
    """Design offset, NOT proof of clearance on a curved finished tile pair.

    Actual finishedFloat32 triangles need sampled overlap clearance (as H1).
    All row placement/overlap lengths remain explicit caller parameters.
    """
    if type(course) is not int or course<0 or not 0<skin_thickness_m<step_m:
        raise ValueError('Tile step must exceed skin thickness')
    return -course*step_m

def camera_hypothesis(photo,anchor,edges):
    meta=photo.get('camera_metadata',{})
    if 'GPSLatitude' not in meta:return {'photo':photo['pageid'],'gps':None,'geographic_face_assignment':None}
    point=[meta['GPSLongitude'],meta['GPSLatitude']];e,n=enu(point,anchor);distance=math.hypot(e,n)
    position_bearing=bearing(e,n)
    ranked=sorted(edges,key=lambda x:abs((x['outward_bearing_deg']-position_bearing+180)%360-180))
    valid_candidate=photo['pageid']==50958259
    return {'photo':photo['pageid'],'recorded_camera_gps':point,'distance_from_source_centroid_m':distance,
            'source_to_recorded_camera_bearing_deg':position_bearing,
            'nearest_outward_normal_edge_ids_if_GPS_correct':[x['edge_id'] for x in ranked[:2]],
            'use':'weak viewpoint hypothesis only; crop, GPS error and floor identity unresolved' if valid_candidate else 'rejected for face assignment; cameraGPS far from local photographed setting',
            'geographic_face_assignment':None,'door_parity_assignment':None}

def plan():
    lock=json.loads((HERE/'reference-lock.json').read_text())
    for item in lock['files']:
        p=HERE/item['file'];assert p.stat().st_size==item['bytes'] and digest(p)==item['sha256']
    source=json.loads((HERE/'references/identity-source-proof.json').read_text())
    photos=json.loads((HERE/'references/photo-register.json').read_text())['photos']
    edges=source_edges(source);anchor=source['source_shape']['centroid_lonlat']
    # Pure logical check. Neither scenario becomes the chosen geographic phase.
    scenarios=[]
    for phase in (0,1):
        levels=[]
        for level in range(1,8):
            row=[opening_kind(level,e,first_level_open_parity=phase) for e in range(8)]
            assert row.count('through_cusped_door')==row.count('blind_rectangular_niche')==4
            levels.append(row)
        scenarios.append({'first_level_open_parity':phase,'levels':levels})
    return {'schema':'longhua-analytic-design-plan-v1','status':'DESIGN_ONLY_NO_ASSET',
        'coordinate_system':'East,North,Up metres; glTF conversion reserved for future frozen exporter',
        'reference_lock_sha256':digest(HERE/'reference-lock.json'),
        'source_boundary':source['raw']['feature']['geometry'],'anchor':anchor,'source_edges':edges,
        'footprint_role':'original ownerboundary retained exactly; wall/eave/plinth interpretation remains unknown',
        'documented_nominal_heights_m':{'tower_body':32.3,'body_and_finial':40.64,'not_a_survey':True,'other_official_records':[40.6,41.4]},
        'geographic_front_edge':None,'opening_phase_chosen':None,
        'camera_hypotheses':[camera_hypothesis(p,anchor,edges) for p in photos],
        'unselected_opening_scenarios':scenarios,
        'level_plan':[{'level':i,'visible_principal_eave_count':1,'wall_base_z_m':None,'wall_top_z_m':None,
                       'wall_scale_from_source':None,'balcony_scale_from_source':None,'roof_scale_from_source':None,
                       'eave_inner_z_m':None,'eave_mid_z_m':None,'corner_lift_m':None,
                       'interpretation':'basearcade largely occluded; no invented steps' if i==1 else 'upperlevel with actualopen geometricbalcony',
                       'openings':'4through/4blind alternating; geographic phase unresolved'} for i in range(1,8)],
        'highest_roof_inner_or_crown_z_m':32.3,'finial_top_z_m':40.64,
        'height_baseline_note':'These two nominal tops are proposal coordinate placeholders using ground0; actual shared datum not established.',
        'generation_prohibited_here':['rawGLB','webGLB','LODGLB','nativeBlend','browser','Blender','mainwrite','Git'],
        'model_acceptance':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--emit-plan',type=Path,required=True,help='New JSON inside this isolated stage only; no models generated')
    a=p.parse_args();dest=a.emit_plan.resolve()
    if dest.suffix!='.json' or not dest.is_relative_to(HERE) or dest.exists():
        p.error('Only a new .json file inside this stage is permitted')
    value=plan();dest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'file':str(dest),'bytes':dest.stat().st_size,'sha256':digest(dest),'asset_generated':False}))

if __name__=='__main__':main()
