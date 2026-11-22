"""Register the southwest garden tower and the first open loggia against the two original city meshes."""
import argparse
from pathlib import Path
import sys

import numpy as np
import shapely as geo
from shapely.geometry import Point, Polygon, box, shape, MultiLineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='jingan-rong-residence-garden-tower'
OWNER=749


def public_ground_obstacles(site):
    """A raised walking slab is traversable. Preserve columns, the recessed wall and the closed tower."""
    structures=[]
    for item in read(site.work/'delivered-decode.json'):
        mesh=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        # The projecting column base starts 0.18 m above the garden walk.
        # Clip the original delivered surfaces above the top of that walk and below head height.
        local=mesh[:,:,[0,2,1]]*[1,-1,1]
        z=local[:,:,2]
        sliced=[]
        for tri in local[(z.max(axis=1)>.19)&(z.min(axis=1)<1.95)]:
            face=list(tri)
            for h,above in ((.19,True),(1.95,False)):
                nxt=[]
                for a,b in zip(face,face[1:]+face[:1]):
                    at=a[2]>=h if above else a[2]<=h
                    bt=b[2]>=h if above else b[2]<=h
                    if at:nxt.append(a)
                    if at!=bt:nxt.append(a+(b-a)*(h-a[2])/(b[2]-a[2]))
                face=nxt
            if len(face)>=3:
                poly=Polygon(np.asarray(face)[:,:2])
                if poly.is_valid and poly.area>1e-8:sliced.append(poly)
        # A vertical wall has no area when projected onto the ground. Intersect
        # complete watertight walls and sash leaves with pedestrian-height planes.
        for height in (.241,.62,1.28,1.83):
            crossed=local[(z.max(axis=1)>height)&(z.min(axis=1)<height)]
            lines=[]
            for tri in crossed:
                ends=[]
                for p,q in zip(tri,np.roll(tri,-1,axis=0)):
                    if (p[2]<=height<q[2])or(q[2]<=height<p[2]):
                        ends.append((p+(q-p)*((height-p[2])/(q[2]-p[2])))[:2])
                if len(ends)==2 and np.linalg.norm(ends[0]-ends[1])>.00001:
                    lines.append(np.asarray(ends).round(5))
            if lines:
                contours=geo.polygonize(geo.linestrings(np.asarray(lines)))
                sliced.extend(contours.geoms)
        structures.extend(sliced)
    # People cannot enter through the closed garden-facing sashes.
    tower=Polygon([(-1.65,0),(1.65,0),(2.78,2.893),(2.78,4.713),(-2.78,4.713),(-2.78,2.893)])
    structures.append(tower)
    # Shallow triangular surface projections can leave submillimetre mesh seams.
    merged=geo.union_all(structures,grid_size=.002).buffer(.008,join_style='mitre').buffer(-.008,join_style='mitre')
    return merged.simplify(.002,preserve_topology=True)


def line_segments(cut,outline):
    result=[]
    for line in geo.get_parts(geo.line_merge(cut.boundary.intersection(outline))):
        for a,b in zip(line.coords,list(line.coords)[1:]):
            if np.linalg.norm(np.asarray(a)-b)>.007:result.append([a,b])
    assert result
    return MultiLineString(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    review_path=PROJECT/'source/precise'/ID/'footprint-review.json'
    review=read(review_path);site=PlacementMeshes(PROJECT,args.work,review)
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs')).strip()
    assets,bounds,form,_=site.decode_model(args.manifest)
    cut=box(-4.85,-5.0,6.99,6.07)
    assert cut.covers(form),form.difference(cut).area
    group,=review['near_tiles']
    original=site.decode_group(group,OWNER)
    surfaces={};seams={};tops={}
    for role,(own,other,assignment)in original.items():
        old=site.project_faces(own);remaining=old.difference(cut)
        touches=geo.intersects(cut,geo.polygons(own[:,:,:2]))
        other_shape=site.project_faces(other)
        distance=other_shape.distance(cut)
        kept=remaining.area/old.area
        assert .78<kept<.89 and distance>3,(role,kept,distance)
        assert np.count_nonzero(touches)>0 and cut.intersection(other_shape).is_empty
        tops[role]=float(own[touches,:,2].max())
        assert 24<tops[role]<28,(role,tops[role])
        seams[role]=line_segments(cut,old)
        surfaces[role]=dict(assignment=assignment,source_triangles=len(own),affected_source_triangles=int(touches.sum()),unchanged_other_group_triangles=len(other),other_source_distance_m=distance,source_projected_m2=old.area,retained_m2=remaining.area,retained_percent=100*kept,source_roof_m=tops[role],mask_seam_m=seams[role].length)
    agreement=seams['far'].hausdorff_distance(seams['near'])
    assert agreement<.42 and abs(tops['near']-tops['far'])<.1,(agreement,tops)
    ready=read(site.files['READY.json'])
    caps=dict(geometry=site.wgs(seams['far']),base_m=0,roof_m=tops['far'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    neighbors=[]
    for j in review['selection']['checked_neighbors']:
        outline=site.footprints[j];d=outline.distance(cut)
        assert d>3
        record=next(f for f in review['owners']if f['local_id']==j)
        neighbors.append(dict(owner=j,source_distance_m=d,model_distance_m=outline.distance(form),mask_distance_m=d,remaining=True,center_wgs84=list(shape(record['geometry_wgs84']).representative_point().coords[0])))
    collide=public_ground_obstacles(site);source=site.footprints[OWNER]
    probes=[]
    def probe(name,x,y,inside,mapblocked):
        pt=Point(x,y);obstacle=collide.covers(pt);blocked=obstacle or (not cut.covers(pt)and source.covers(pt))
        assert (obstacle,blocked)==(inside,mapblocked),(name,x,y,obstacle,blocked)
        probes.append(dict(name=name,xy=[x,y],wgs84=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_obstacle=obstacle,source_cut=cut.covers(pt),expected_map='building'if blocked else None))
    for x in [-4,-3,-1.5,0,1.5,3.,4.4,5.7,6.6]:
        for y in [-3.8,-1.]:probe('Open south garden',x,y,False,False)
    for x,y in [(-1.2,.12),(0,.14),(1.2,.19),(-2.05,2),(2.05,2),(0,3),(0,4.50)]:
        probe('Closed historic tower',x,y,True,True)
    for x in [2.9,6.44]:probe('Lower loggia column and plinth',x,3.273,True,True)
    for x in [3.36,4.02,4.63,5.26,5.88]:
        for y in [3.273,4.15,5.10]:probe('Open first loggia walking slab',x,y,False,False)
    for x in [3.15,3.8,5.55,6.2]:probe('Rear loggia wall',x,5.8,True,True)
    for x,y in [(-2.8,7.3),(-1,7.1),(2.1,7.4),(5.5,7.4),(7.6,3.5),(10,3.5),(14,3.5)]:
        probe('Original mansion beyond photographed first bay',x,y,False,True)
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),source_feature_ids={'building':[review['owner']['source_key'][9:]],'building_part':[]},replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collide),source_section_caps=caps,lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},bounds_glb=bounds,overviewBearing=-42.,overviewPitch=56.,overviewZoom=19.0,maxDistance=740,lod_switch_in_m=875,lod_switch_out_m=1050,navigation={'listed':False,'status':'由东南花园看西南角塔的三折面、铜色圆顶和相邻一间双层敞廊。'},placement={'status':'map-aligned','note':'依两处航照与两次地面照片估计角塔位置，院内定位误差约4米。仅替换原城749西南角及首间柱廊，其他主楼和邻屋保留。'},partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['collision_geometry'],'Rong residence garden tower and loggia',collision=True);checked_geometry(contract['replacement_geometry'],'Rong residence southwest corner')
    result=dict(id=ID,manifest_sha256=sha(args.manifest),source_sha256=sha(review_path),checker_sha256=sha(Path(__file__)),mesh_decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py'),assets=assets,model_projected_m2=form.area,collision_m2=collide.area,mask_m2=cut.area,source_variants=surfaces,seam_agreement_m=agreement,cap_segments=len(seams['far'].geoms),neighbors=neighbors,ground_probes=probes)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',result)
    print('Retained area, both city meshes',surfaces,'ground probes',len(probes),flush=True)

if __name__=='__main__':main()
