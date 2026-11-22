"""Compare the west porch with its original city block and adjoining properties in both city mesh levels."""
from pathlib import Path
import argparse,sys,math,subprocess
import numpy as np
import shapely as geo
from shapely.geometry import shape,box,Polygon,Point,MultiLineString,LineString
HERE=Path(__file__).resolve().parent
PROJECT=Path(__import__('os').environ['SHANGHAI_PROJECT_ROOT']) if 'SHANGHAI_PROJECT_ROOT' in __import__('os').environ else HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='jingan-xinen-church-west-porch'
OWNER=3149


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


def decode_corner_group(site,group,cut):
    ids=np.asarray(group['feature_local_ids'],int)
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':int(i)} for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,
                   stdout=subprocess.DEVNULL)

    def triangles(role):
        mesh=np.fromfile(site.work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        mesh[:,:,:2]=mesh[:,:,:2] @ site.axes.T
        return mesh

    far=triangles('far')
    by_feature=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
    assert len(by_feature)==len(far) and set(by_feature)==set(ids)
    far_outlines={i:site.project_faces(far[by_feature==i]) for i in ids}
    mesh=triangles('near')
    centroids=geo.points(mesh[:,:,:2].mean(1))
    vertices=geo.points(mesh[:,:,:2].reshape(-1,2))
    # Compare each affected near triangle against both feature layers, using
    # face centres as well as all three vertices.
    affected=geo.intersects(cut,geo.polygons(mesh[:,:,:2]))
    selection=None
    methods={}
    for label,points,polygons in [('original_centroid',centroids,site.footprints),
                                  ('far_feature_centroid',centroids,far_outlines),
                                  ('original_mean_vertex',vertices,site.footprints)]:
        distances=np.column_stack([geo.distance(points,polygons[i]) for i in ids])
        if points is vertices:distances=distances.reshape(-1,3,len(ids)).mean(1)
        own=ids[distances.argmin(1)]==OWNER
        if selection is None:selection=own
        contested=selection!=own
        assert not np.any(affected&contested) and np.all(own[affected]),label
        ranked=np.sort(distances[affected],axis=1)
        maximum=float(ranked[:,0].max())
        margin=float(np.diff(ranked[:,:2],axis=1).min())
        assert maximum<.4 and margin>1.45*maximum,(label,maximum,margin)
        methods[label]={'affected_count':int(affected.sum()),'affected_max_own_distance_m':maximum,
                        'affected_min_next_owner_margin_m':margin,'unchanged_disagreements_outside':int(contested.sum())}
    far_target=by_feature==OWNER
    return {'near':(mesh[selection],mesh[~selection],{'assignment_comparisons':methods,
                    'triangles_all_group_owners':len(mesh),'identical_assignments_on_every_affected_triangle':True}),
            'far':(far[far_target],far[~far_target],{'method':'per-vertex _FEATURE_ID_0'})}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    opts=parser.parse_args();opts.out.mkdir(parents=True,exist_ok=True)
    review_path=Path(__import__('os').environ.get('XINEN_FOOTPRINT',PROJECT/'source/precise'/ID/'footprint-review.json'))
    ref=read(review_path);site=PlacementMeshes(PROJECT,opts.work,ref)
    def link_input(name, source):
        # An unlinked seekable RAM file remains readable via its live /proc handle.
        # Keeping the named source also works for ordinary registered delivery files.
        dst=site.work/name
        dst.unlink(missing_ok=True)
        dst.symlink_to(source.absolute())
    site.link=link_input
    image_decoder=PROJECT/'data/audit'/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(image_decoder)).strip()
    assets,bounds,form,physical=site.decode_model(opts.manifest)
    cut=box(-6.53,-.40,6.46,7.63)
    assert cut.is_valid and cut.covers(form),form.difference(cut).area
    group,=ref['near_tiles']
    assert set(group['feature_local_ids'])=={1683,3149,2669,266,2723,470,429}
    decoded=decode_corner_group(site,group,cut)
    src=site.footprints[OWNER]
    # The thin accessible paving lies below the shoe. Project the remaining
    # triangle faces to head height, from every physically decoded delivery.
    role_ground={}
    for result in read(site.work/'delivered-decode.json'):
        indices=np.fromfile(result['triangle_material_ids_file'],np.uint16)
        tris=np.fromfile(result['triangle_file'],np.float64).reshape(-1,3,3)
        local=tris[:,:,[0,2,1]]*[1,-1,1]
        pavement=indices==result['material_names'].index('paving')
        assert pavement.any() and local[pavement,:,2].max()<.08
        role_ground[result['variant']]=site.ground_faces(local[~pavement])
    collision=geo.union_all(list(role_ground.values()),grid_size=.001).buffer(.004,join_style='mitre').buffer(-.004,join_style='mitre').simplify(.003)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 14.5<tops[variant]<15.6,(variant,tops[variant])
        assert remain.area<.01 and affected==len(owned),(variant,remain.area,area.area)
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>2.0

        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':0}
    assert abs(tops['near']-tops['far'])<.08,tops
    nearbys=[]
    for i in ref['selection']['checked_neighbors']:
        fp=site.footprints[i];assert fp.distance(cut)>2.0
        nearbys.append({'owner':i,'model_distance_m':fp.distance(form),'mask_distance_m':fp.distance(cut),'center_wgs84':list(shape(ref['owners'][next(j for j,o in enumerate(ref['owners'])if o['local_id']==i)]['geometry_wgs84']).representative_point().coords[0]),'remaining':True})
    points=[]
    def probe(name,x,y,solid,map_solid):
        pt=Point(x,y);actual=collision.covers(pt);blocked=actual or (not cut.covers(pt) and src.covers(pt))
        assert actual==solid and blocked==map_solid,(name,x,y,actual,blocked)
        for role,footprint in role_ground.items():
            assert footprint.covers(pt)==solid,(role,name,x,y)
        points.append({'name':name,'xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':actual,'source_cut':cut.covers(pt),'expected_map':'building'if blocked else None})
    for x in [-6.6,-5.,-3.66,-2.,0,2.,3.66,5.,6.4]:
        probe(f'Open street courtyard {x}',x,-1.15,False,False)
    for x in [-4.3,-3.66,-3.42,-2.2,-.5,0,1.3,3.42,3.66,4.3]:
        for y in [1.59,3.18,4.75]:
            probe(f'North-to-south open passage {x}/{y}',x,y,False,False)
    for x in [-3.44,-2.8,-1.68,0.,1.7,2.85,3.44]:
        probe(f'West screen below aperture {x}',x,.16,True,True)
    for x in [-3.49,3.49]:
        for y in [.51,.83,5.57,5.94]:
            probe(f'Arcade masonry pier {x}/{y}',x,y,True,True)
    for x in [-5.52,-4.12,-2.18,0,2.13,4.51,5.55]:
        probe(f'Gable main wall {x}',x,6.52,True,True)
    for x,y in [(-5.86,.55),(-5.50,2.8),(-5.15,5.87),(-4.66,3.82),(-4.2,1.02)]:
        assert src.contains(Point(x,y))
        probe(f'Cleared part of misaligned old block {x}/{y}',x,y,False,False)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':76.,'overviewPitch':57,'overviewZoom':19.4,
        'maxDistance':740,'lod_switch_in_m':875,'lod_switch_out_m':1050,'navigation':{'listed':False,'status':'自西南侧街口看三字开孔、门廊南券、三分尖拱窗和山墙十字。'},
        'placement':{'status':'map-aligned','note':'仅纠正简化原体3149偏至门廊北侧的整块。以两侧券门围合步道和后退山墙替入，周围原城建筑保留；礼堂内室、翼部与其他地块另列。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Xinen west and side opening obstacles',collision=True);checked_geometry(contract['replacement_geometry'],'Xinen owner-scoped source cut')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':0,'cap_segments':0,'walkable_paving_max_m':.075,'lod_collision_areas_m2':{k:v.area for k,v in role_ground.items()},'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
