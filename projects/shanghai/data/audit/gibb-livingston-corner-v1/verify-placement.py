"""Verify the photographed southeast corner against the native near and far meshes for the single retained owner."""
from pathlib import Path
import argparse,sys,math
import numpy as np
import shapely as geo
from shapely.geometry import box,Point,MultiLineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-gibb-livingston-corner'
OWNER=102


def cap_on_boundary(cut,projection):
    raw=cut.boundary.intersection(projection)
    parts=geo.get_parts(geo.line_merge(raw))
    lines=[]
    for line in parts:
        coords=list(line.coords)
        for a,b in zip(coords,coords[1:]):
            if math.dist(a,b)>.003:lines.append([a,b])
    result=MultiLineString(lines)
    assert not result.is_empty and cut.boundary.buffer(.00002).covers(result)
    return result



def decode_corner_group(site, group, owner):
    import subprocess
    ids = np.asarray(group['feature_local_ids'])
    site.link('baseline-far.glb', site.files['far.glb'])
    site.link('baseline-near.glb.gz', site.files[Path(group['file']).name])
    site.link('macro-READY.json', site.files['READY.json'])
    write(site.work/'context-features.json', [{'localId':int(i)} for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    result = {}
    for level in ('far','near'):
        tri=np.fromfile(site.work/('baseline-'+level+'-triangles.f64'),np.float64).reshape(-1,3,3)
        tri[:,:,:2] = tri[:,:,:2] @ site.axes.T
        if level=='far':
            labels=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            method={'method':'per-vertex source feature IDs'}
        else:
            centroids=geo.points(tri[:,:,:2].mean(1))
            distances=np.stack([geo.distance(centroids,site.footprints[int(i)])for i in ids],axis=1)
            labels=ids[distances.argmin(1)]
            own=tri[labels==owner];peers=tri[labels!=owner]
            own_vertices=geo.points(own[:,:,:2].reshape(-1,2));all_foreign=geo.union_all([site.footprints[int(i)]for i in ids if i!=owner])
            edge_error=float(np.max(geo.distance(own_vertices,site.footprints[owner])))
            foreign_space=float(np.min(geo.distance(own_vertices,all_foreign)))
            sorted_dist=np.sort(distances[labels==owner],axis=1)
            margin=float(np.min(sorted_dist[:,1]-sorted_dist[:,0]))
            far_body=site.project_faces(result['far'][0])
            far_agreement=float(np.max(geo.distance(own_vertices,far_body)))
            foreign_near=site.project_faces(peers)
            independent_clearance=foreign_near.distance(far_body)
            assert edge_error<.42 and far_agreement<.47,(edge_error,far_agreement)
            assert margin>1.25 and foreign_space>edge_error*5 and independent_clearance>.50,(margin,foreign_space,edge_error,independent_clearance)
            method=dict(method='Seven source rings, actual near vertices and the separately ID-tagged far mesh',
                        maximum_own_vertex_deviation_m=edge_error,nearest_foreign_polygon_m=foreign_space,
                        minimum_centroid_margin_m=margin,maximum_distance_to_typed_far_mesh_m=far_agreement,
                        minimum_other_near_to_typed_far_m=independent_clearance)
        assert set(labels)==set(ids)
        result[level]=(tri[labels==owner],tri[labels!=owner],method)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    opts=parser.parse_args();opts.out.mkdir(parents=True,exist_ok=True)
    review_path=PROJECT/'source/precise'/ID/'footprint-review.json'
    ref=read(review_path);site=PlacementMeshes(PROJECT,opts.work,ref)
    assets,bounds,form,physical=site.decode_model(opts.manifest)
    cut=geo.union_all([box(-10.32,-2.65,2.68,.70),box(-1.35,-2.65,2.68,9.89)])
    # Remove intersection vertices that lie in the middle of a straight street edge.
    # The six exterior corners give the renderer four triangles in geographic coordinates.
    simple_cut=cut.simplify(.000001, preserve_topology=True)
    assert simple_cut.equals(cut) and len(simple_cut.exterior.coords)==7
    cut=simple_cut
    assert cut.covers(form),(form.bounds,cut.bounds)
    groups=ref['near_tiles'];assert len(groups)==1 and set(groups[0]['feature_local_ids'])=={2134,1751,874,2969,2026,3157,102}
    decoded=decode_corner_group(site,groups[0],OWNER)
    src=site.footprints[OWNER]
    # Preserve the existing solid street-wall interior within the bounded replacement.
    # Ground collision follows the delivered facade plinth beyond that original outline.
    inset=cut.intersection(src)
    collision=geo.union_all([inset,physical],grid_size=.001).buffer(.018,join_style=2).buffer(-.018,join_style=2).simplify(.010)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 10<=tops[variant]<=18
        assert .78<remain.area/area.area<.995
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>.5
        seams[variant]=cap_on_boundary(cut,area)
        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':seams[variant].length}
    agreement=seams['far'].hausdorff_distance(seams['near']);assert agreement<.21,agreement
    assert abs(tops['near']-tops['far'])<.06,tops
    ready=read(site.files['READY.json'])
    caps={'geometry':site.wgs(seams['far']),'base_m':0,'roof_m':tops['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(site.files['far.glb'])}
    nearbys=[]
    for i in ref['selection']['checked_neighbors']:
        fp=site.footprints[i];assert fp.distance(cut)>.40
        nearbys.append({'owner':i,'model_distance_m':fp.distance(form),'mask_distance_m':fp.distance(cut),'remaining':True})
    points=[]
    def probe(name,x,y,solid,map_solid):
        pt=Point(x,y);actual=collision.covers(pt);blocked=actual or (not cut.covers(pt) and src.covers(pt))
        assert actual==solid and blocked==map_solid,(name,x,y,actual,blocked)
        points.append({'name':name,'xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':actual,'source_cut':cut.covers(pt),'expected_map':'building'if blocked else None})
    for angle in (-142,-103,-64,-25,15,47):
        x=math.cos(math.radians(angle));y=math.sin(math.radians(angle))
        probe('inside ground-floor drum',x*1.86,y*1.86,True,True)
        probe('footpath outside curved plinth',x*2.70,y*2.70,False,False)
    for x in (-9,-6,-3.1):
        probe('south wall interior',x,-.44,True,True)
        probe('Dianchi Road pavement',x,-1.27,False,False)
    for y in (2.9,5.2,8.2):
        probe('east wall interior',.65,y,True,True)
        probe('east street pavement',1.57,y,False,False)
    probe('existing main building beyond mask',-4,4,False,True)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':-43,'overviewPitch':37,'overviewZoom':20.13,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从路口看红砖圆角、上层阳台和鼓座。'},
        'placement':{'status':'map-aligned','note':'以100号实名地块街口的圆弧拟合圆心，按两侧实际街线落位，限圆角和两段短街墙。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Gibb Livingston corner collision',collision=True);checked_geometry(contract['replacement_geometry'],'Gibb Livingston street corner mask')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
