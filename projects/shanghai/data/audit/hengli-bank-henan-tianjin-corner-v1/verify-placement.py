"""Verify both streets and the chamfer against the original Hengli Bank and neighboring properties."""
from pathlib import Path
import argparse,sys,math,subprocess
import numpy as np
import shapely as geo
from shapely.geometry import shape,box,Polygon,Point,MultiLineString,LineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-hengli-bank-henan-tianjin-corner'
OWNER=2272


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
    # Two properties share their northern cadastral boundary. Resolve all affected
    # triangles three ways. Exterior uncertainties, retained at full geometry, are
    # counted explicitly; no assignment near the shared edge is assumed.
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
        assert maximum<.12 and margin>1.5*maximum,(label,maximum,margin)
        methods[label]={'affected_count':int(affected.sum()),'affected_max_own_distance_m':maximum,
                        'affected_min_next_owner_margin_m':margin,'unchanged_disagreements_outside':int(contested.sum())}
    far_target=by_feature==OWNER
    return {'near':(mesh[selection],mesh[~selection],{'assignment_comparisons':methods,
                    'triangles_all_seven_owners':len(mesh),'identical_assignments_on_every_affected_triangle':True}),
            'far':(far[far_target],far[~far_target],{'method':'per-vertex _FEATURE_ID_0'})}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    opts=parser.parse_args();opts.out.mkdir(parents=True,exist_ok=True)
    review_path=PROJECT/'source/precise'/ID/'footprint-review.json'
    ref=read(review_path);site=PlacementMeshes(PROJECT,opts.work,ref)
    image_decoder=HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(image_decoder)).strip()
    assets,bounds,form,physical=site.decode_model(opts.manifest)
    cut=Polygon([(-16.13,3.92),(-16.00,-.66),(.35,-.67),(3.64,3.12),(1.66,32.10),
                 (-1.71,31.92),(-.78,18.73),(-3.03,18.53),(-2.85,16.18),(-11.89,16.18),
                 (-11.89,6.92),(-12.26,6.92),(-12.26,3.92)])
    assert cut.is_valid and cut.covers(form),form.difference(cut).area
    group,=ref['near_tiles']
    assert set(group['feature_local_ids'])=={1636,1272,2651,654,909,2272,1992}
    decoded=decode_corner_group(site,group,cut)
    src=site.footprints[OWNER]
    solid=geo.union_all([src.intersection(cut),physical],grid_size=.001)
    outline=ref['local_outline']
    faces={'Tianjin':(outline[2],outline[1]),'Chamfer':(outline[1],outline[0]),'Henan':(outline[0],outline[4])}
    def position(side,station,depth):
        a,b=map(np.asarray,faces[side]);t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]])
        return (a+b)/2+station*t+depth*n
    gates=[('Chamfer',0,.91,-.21),('Henan',-29.20857/2+13.55,.85,-.215),('Henan',29.20857/2-1.32,.57,-.14)]
    pockets=[Polygon([position(side,x+dx,z) for dx,z in [(-w,.74),(w,.74),(w,d),(-w,d)]])for side,x,w,d in gates]
    collision=solid.difference(geo.union_all(pockets)).buffer(.012,join_style='mitre').buffer(-.012,join_style='mitre').simplify(.004)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 25.50<=tops[variant]<=25.70
        assert .44<remain.area/area.area<.55
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>.16
        seams[variant]=cap_on_boundary(cut,area)
        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':seams[variant].length}
    agreement=seams['far'].hausdorff_distance(seams['near']);assert agreement<.22,agreement
    assert abs(tops['near']-tops['far'])<.06,tops
    ready=read(site.files['READY.json'])
    caps={'geometry':site.wgs(seams['far']),'base_m':0,'roof_m':tops['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(site.files['far.glb'])}
    nearbys=[]
    for i in ref['selection']['checked_neighbors']:
        fp=site.footprints[i];assert fp.distance(cut)>.16
        nearbys.append({'owner':i,'model_distance_m':fp.distance(form),'mask_distance_m':fp.distance(cut),'center_wgs84':list(shape(ref['owners'][next(j for j,o in enumerate(ref['owners'])if o['local_id']==i)]['geometry_wgs84']).representative_point().coords[0]),'remaining':True})
    points=[]
    def probe(name,x,y,solid,map_solid):
        pt=Point(x,y);actual=collision.covers(pt);blocked=actual or (not cut.covers(pt) and src.covers(pt))
        assert actual==solid and blocked==map_solid,(name,x,y,actual,blocked)
        points.append({'name':name,'xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':actual,'source_cut':cut.covers(pt),'expected_map':'building'if blocked else None})
    for side,stations in [('Tianjin',[-7.,-4.9,-2.7,.1,2.5,5.2]),('Henan',[-13.,-10.,-6.4,-3.2,2.5,5.9,9.2,11.3]),('Chamfer',[-1.48,1.54])]:
        for station in stations:
            probe(f'{side} pavement {station}',*position(side,station,1.03),False,False)
            probe(f'{side} street wall {station}',*position(side,station,-.45),True,True)
    for side,station,width,depth in gates:
        for dx in [-width*.55,width*.55]:
            probe(f'{side} approach {station+dx:.2f}',*position(side,station+dx,depth+.065),False,False)
            probe(f'{side} closed door {station+dx:.2f}',*position(side,station+dx,depth-.08),True,True)
    probe('Original retained northern core',-9.40,24.0,False,True)
    probe('Original retained western block',-13.50,13.0,False,True)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':-44.,'overviewPitch':44,'overviewZoom':18.92,
        'maxDistance':610,'lod_switch_in_m':815,'lod_switch_out_m':960,'navigation':{'listed':False,'status':'从天津路和河南中路路口看棕砖斜门、两面浅色竖窗和高起退台。'},
        'placement':{'status':'map-aligned','note':'仅更新2272的两条临街窗墙、斜角及可见上部，后身约半幅仍保留原城。北端以未动的接缝衔接909号原房。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Hengli street entrance thresholds',collision=True);checked_geometry(contract['replacement_geometry'],'Hengli east and south fronts')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
