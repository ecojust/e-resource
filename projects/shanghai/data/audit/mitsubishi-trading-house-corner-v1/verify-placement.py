"""Verify the photographed southwest round tower against the native near and far meshes for the single retained owner."""
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
ID='huangpu-mitsubishi-trading-house-round-corner'
OWNER=302


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



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    opts=parser.parse_args();opts.out.mkdir(parents=True,exist_ok=True)
    review_path=PROJECT/'source/precise'/ID/'footprint-review.json'
    ref=read(review_path);site=PlacementMeshes(PROJECT,opts.work,ref)
    assets,bounds,form,physical=site.decode_model(opts.manifest)
    cut=box(-3.01,-3.04,3.01,2.77)
    assert cut.covers(form), (form.bounds,cut.bounds)
    groups=ref['near_tiles']
    assert len(groups)==1 and set(groups[0]['feature_local_ids'])=={1037,825,1289,561,302,2418}
    decoded=site.decode_group(groups[0],OWNER)
    src=site.footprints[OWNER]
    section=__import__('runpy').run_path(str(HERE.parent/'sino-french-school-v1/verify-placement.py'))['solid_section']
    ground=[]
    for item in read(site.work/'delivered-decode.json'):
        triangles=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        local=triangles[:,:,[0,2,1]]*[1,-1,1]
        ground.append(section(local,.553))
    # Keep the enclosed room inside the old block; the front step stays accessible up to the closed door.
    room=src.intersection(cut).intersection(box(-3.1,-1.075,3.1,3.1))
    collision=geo.union_all([room,*ground],grid_size=.001).simplify(.005,preserve_topology=True)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 25.5<=tops[variant]<=25.7
        assert .94<remain.area/area.area<.99
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
    for x in (-.93, -.43, .37, .88):
        probe('street approach',x,-3.31,False,False)
        probe('open front step',x,-1.26,False,False)
        probe('closed wooden double door',x,-1.085,True,True)
        probe('room behind the door',x,.51,True,True)
    for x in (-2.04,-1.64,1.59,2.10):
        probe('solid ground-floor masonry',x,-1.34,True,True)
    for x in (-1.1,0,1.1):
        probe('retained existing building',x,4.67,False,True)
    for x in (-4.25,4.25):
        probe('outside the short street frontage',x,-2.30,False,False)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':26,'overviewPitch':46,'overviewZoom':19.75,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从广东路与四川中路的街口看底层券门和三窗轴圆塔。'},
        'placement':{'status':'map-aligned','note':'依据广东路102号所在地块的两条街线和东北角圆鼓顶投影定位。仅替换西南转角冠部与平切券门对应的小段，保存两个临街长翼。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Guangdong Road closed doorway',collision=True);checked_geometry(contract['replacement_geometry'],'Guangdong Road tower cut')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
