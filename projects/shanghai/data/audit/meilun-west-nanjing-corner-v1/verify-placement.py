"""Verify Meilun’s two short street fronts and the shop recesses against the near and far city meshes."""
from pathlib import Path
import argparse,sys,math
import numpy as np
import shapely as geo
from shapely.geometry import Polygon,Point,MultiLineString,LineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-meilun-west-nanjing-corner'
OWNER=1562


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
    layout=read(review_path.parent/'corner-study.json')['corner']
    n,w=layout['nanjing_end'],layout['west_end']
    edges=[([n[0]+12.8,n[1]],n,2,.74,'Nanjing'),(n,w,1,.86,'diagonal'),
           (w,layout['west_study_end'],1,.67,'Jiangxi')]
    street=LineString([edges[0][0],n,w,edges[2][1]])
    cut=street.buffer(1.72,cap_style='square',join_style='mitre')
    assert cut.covers(form)
    groups=ref['near_tiles']
    assert len(groups)==1 and set(groups[0]['feature_local_ids'])=={2945,738,1562,714}
    decoded=site.decode_group(groups[0],OWNER)
    src=site.footprints[OWNER]
    # A horizontal threshold at 0.125 m is walkable. The midpoint of each
    # opening is physically open up to the inset shopfront, checked by rays.
    # Stone jambs and the enclosed volume behind the glass remain obstacles.
    bays=[]
    mouths=[]
    for a,b,count,setback,label in edges:
        a,b=np.array(a),np.array(b)
        length=float(np.linalg.norm(b-a));t=(b-a)/length;normal=np.array([t[1],-t[0]])
        for i in range(count):
            ctr=(a+b)/2+t*(-length/2+length/count*(i+.5))
            half=(length/count-.82)/2-.07
            corners=[ctr+t*u+normal*d for u,d in [(-half,.72),(half,.72),(half,-setback-.13),(-half,-setback-.13)]]
            mouths.append(Polygon(corners))
            bays.append((label+' '+str(i+1),ctr,t,normal,setback,half))
    solid=geo.union_all([cut.intersection(src),physical],grid_size=.001)
    collision=solid.difference(geo.union_all(mouths)).buffer(.012,join_style=2).buffer(-.012,join_style=2).simplify(.006)
    seen={};seams={};tops={}
    for variant,(owned,other,assigned) in decoded.items():
        area=site.project_faces(owned);remain=area.difference(cut)
        near=geo.intersects(cut,geo.polygons(owned[:,:,:2]))
        affected=int(near.sum());assert affected>0
        tops[variant]=float(owned[near,:,2].max())
        assert 20.73<=tops[variant]<=20.77
        assert .96<remain.area/area.area<.99
        other_distance=site.project_faces(other).distance(cut)if len(other)else None
        assert other_distance is None or other_distance>.5
        seams[variant]=cap_on_boundary(cut,area)
        seen[variant]={'assignment':assigned,'source_triangles':len(owned),'affected_source_triangles':affected,'unchanged_other_group_triangles':len(other),'other_source_distance_m':other_distance,'source_projected_m2':area.area,'retained_m2':remain.area,'retained_percent':remain.area*100/area.area,'source_roof_m':tops[variant],'mask_seam_m':seams[variant].length}
    agreement=seams['far'].hausdorff_distance(seams['near']);assert agreement<.26,agreement
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
    for label,center,t,norm,setback,half in bays:
        def local_probe(name,offset,side,solid,blocked):
            x,y=center+norm*offset+t*side
            probe(label+' '+name,float(x),float(y),solid,blocked)
        local_probe('open pavement',1.94,0,False,False)
        local_probe('open shop threshold before glass',-.48,.22,False,False)
        local_probe('recessed glazing and enclosed shop',-setback-.32,.18,True,True)
        local_probe('rusticated bordering pier',.105,half+.18,True,True)
        local_probe('retained block behind facade',-4.4,0,False,True)
    for x,y in [(-5.0,3.2),(-5.5,-4.2),(10.2,4.4)]:
        probe('pedestrian space in adjoining streets',x,y,False,False)
    row=next(v for v in ref['owners']if v['local_id']==OWNER)
    contract={'id':ID,'owner':{'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(collision),'source_section_caps':caps,'lng':site.lon,'lat':site.lat,'heading':ref['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'overviewBearing':132.,'overviewPitch':38,'overviewZoom':20.15,
        'maxDistance':435,'lod_switch_in_m':610,'lod_switch_out_m':745,'navigation':{'listed':False,'status':'从南京东路与江西中路交叉口看西楼两道山花、临街石窗和店面退进。'},
        'placement':{'status':'map-aligned','note':'按具名源面1562的西北转角两端落位，保留西楼大部原有屋面、内街与南京东路181号邻楼。'},
        'partial_model':True,'model_scope':read(opts.manifest)['scope']}
    checked_geometry(contract['collision_geometry'],'Meilun shopfront collision',collision=True);checked_geometry(contract['replacement_geometry'],'161 Nanjing Road corner mask')
    write(opts.out/'final-placement-contract.json',contract)
    write(opts.out/'placement-geometry.json',{'id':ID,'manifest_sha256':sha(opts.manifest),'source_sha256':sha(review_path),'checker_sha256':sha(Path(__file__)),'mesh_decoder_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'assets':assets,'model_projected_m2':form.area,'collision_m2':collision.area,'mask_m2':cut.area,'source_variants':seen,'seam_agreement_m':agreement,'cap_segments':len(seams['far'].geoms),'neighbors':nearbys,'ground_probes':points})


if __name__=='__main__':main()
