"""Compare the photographed skyline, stone dentils and long window-head ribs with actual GLB surfaces."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

def review(project,source,mesh):
    sys.path.insert(0,str(source))
    from crown_plane import CAMERA,EYE,INVERSE,at_row
    from corner_crown import BRICK,COPING,LIMESTONE,observations
    from street_path import station
    tools=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    tri,ids,names,identity=tools['load_triangles'](mesh)
    xyz=tri.reshape(-1,3);q=xyz@CAMERA[:,:3].T+CAMERA[:,3]
    pts=(q[:,:2]/q[:,2,None]).reshape(-1,3,2);lo=pts.min(axis=1)-.002;hi=pts.max(axis=1)+.002
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    appearance=tools['material_appearance'](mesh)['materials']
    two=np.array([appearance[name]['doubleSided']for name in names])[ids]
    # Surface projection relative to the common surveyed street path.
    marks=np.linspace(-6.,18.,4001);p_and_n=[station(s) for s in marks]
    xy=np.array([c[0]for c in p_and_n]);norm=np.array([c[2]for c in p_and_n]);tree=cKDTree(xy)
    cache={}
    def hit(u,v):
        px=np.array([u,v]);cell=tuple(np.floor(px/32).astype(int))
        if cell not in cache:
            origin=np.array(cell)*32
            cache[cell]=np.flatnonzero(np.all(hi>=origin,axis=1)&np.all(lo<=origin+32,axis=1))
        ray=INVERSE@np.r_[px,1.];ray/=np.linalg.norm(ray)
        items=cache[cell]
        items=items[np.all(lo[items]<=px,axis=1)&np.all(hi[items]>=px,axis=1)&(two[items]|(n[items]@ray<-1.e-11))]
        if not len(items):return None,None
        i,t,point=tools['first_hit'](tri[items],EYE,ray)
        if not np.isfinite(t):return None,None
        j=tree.query(point[:2])[1];projection=(point[:2]-xy[j])@norm[j]
        return names[ids[items[i]]],float(projection)
    data=observations()
    skyline=[]
    for i,line in enumerate(data['roof_sections_px'],1):
        selected=np.unique(np.rint(np.linspace(0,len(line)-1,5)[1:-1]).astype(int))
        row=[]
        for j in selected:
            u,v=line[j];vs=np.arange(v-18.,v+19.,.5)
            hits=[hit(u,dy)[0] for dy in vs]
            found=next((float(dy) for dy,s in zip(vs,hits) if s in [COPING,BRICK,LIMESTONE]),None)
            row.append(dict(source_px=[u,v],mesh_top_v=found,first_surface=None if found is None else hit(u,found)[0],error_px=None if found is None else found-v))
        skyline.append(dict(parapet=i,positions=row))
    slots=[]
    for i,band in enumerate(data['dentil_bands'],1):
        row=[]
        for s in band['slots']:
            x,y=s['centre_px'];a,b=s['left_right_u_px'];mat,depth=hit(x,y)
            sides=[hit(a-1.8,y),hit(b+1.8,y)]
            raised=[d for m,d in sides if m==LIMESTONE]
            d=max(raised)-depth if raised and depth is not None else None
            row.append(dict(source_px=[x,y],front_material=mat,flanking_materials=[m for m,_ in sides],
                            relief_m=round(d,5) if d is not None else None,
                            passed=mat==LIMESTONE and d is not None and d>.010))
        slots.append(dict(band=i,positions=row))
    heads=json.loads((source.parent/'measurements/ribbed-stone-window-heads.json').read_bytes())['panels']
    windows=[]
    for no,panel in enumerate(heads,1):
        grooves=panel['long_flute_shadows'];out=[]
        for i,g in enumerate(grooves):
            x,y=g['native_px'];u=g['u_at_reference_row']
            distance=grooves[min(i+1,len(grooves)-1)]['u_at_reference_row']-u if i<len(grooves)-1 else u-grooves[i-1]['u_at_reference_row']
            # Compare the photographed longitudinal shadow against both adjacent
            # faces on the same panel, including its exposed end returns.
            candidates=[hit(at_row(u+off,930.,y),y) for off in np.arange(-2.,2.1,.5)]
            peaks=[hit(at_row(u+sign*distance*.48,930.,y),y)for sign in [-1,1]]
            in_stone=[d for m,d in candidates if m==LIMESTONE]
            pstone=[d for m,d in peaks if m==LIMESTONE]
            drop=max(pstone)-min(in_stone) if pstone and in_stone else None
            out.append(dict(photo_px=[x,y],relief_m=None if drop is None else round(drop,5),
                            passed=drop is not None and drop>.008))
        windows.append(dict(panel=no,flute_controls=out))
    return dict(mesh=identity,skyline=skyline,dentil_recesses=slots,stone_heads=windows)
def package_review(project,source,folder):
    exports=[('raw','raw.glb','raw.glb'),('web','full.glb','decoded-full.glb'),('lod','lod.glb','decoded-lod.glb')]
    record={}
    for mode,delivered,plain in exports:
        data=review(project,source,folder/plain)
        skyline=[p['error_px'] for g in data['skyline'] for p in g['positions']]
        slots=[p for g in data['dentil_recesses'] for p in g['positions']]
        flutes=[p for g in data['stone_heads'] for p in g['flute_controls']]
        assert len(skyline)==33 and all(v is not None and abs(v)<=3 for v in skyline)
        assert len(slots)==41 and all(p['passed'] for p in slots)
        assert len(flutes)==29 and all(p['passed'] for p in flutes)
        data['summary']={'skyline_controls':len(skyline),'maximum_skyline_difference_native_px':max(map(abs,skyline)),
                         'recesses':len(slots),'minimum_observed_band_relief_m':min(p['relief_m']for p in slots),
                         'long_flutes':len(flutes),'minimum_observed_head_relief_m':min(p['relief_m']for p in flutes)}
        file=folder/delivered
        data['delivered']={'file':delivered,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
        record[mode]=data
    return {'subject':'南京东路257号老介福两街转角塔冠','source':'Upright 3024 x 4032 exposure by Chainwit., April 2024',
            'method':'First visible intersection with the full building mesh in the photo camera. Compare skyline height, recess faces between adjoining projecting stones and long flutes against each side of the same panel. Depths are measured on the reconstruction and estimated from appearance.',
            'registration':'corner-crown-camera.json','feature_survey':'corner-crown-features.json',
            'side_panels':'ribbed-stone-window-heads.json','variants':record}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ['project','source','output']:ap.add_argument('--'+k,type=Path,required=True)
    inputs=ap.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--mesh',type=Path);inputs.add_argument('--package',type=Path)
    a=ap.parse_args()
    r=package_review(a.project,a.source,a.package) if a.package else review(a.project,a.source,a.mesh)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
