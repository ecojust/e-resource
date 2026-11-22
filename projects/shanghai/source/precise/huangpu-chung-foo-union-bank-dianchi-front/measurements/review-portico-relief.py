"""Cast original street-photo rays at the exported column carving and recessed porch ceiling."""
import argparse
import json
import runpy
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Point, Polygon


def check(mesh,project,source):
    sys.path.insert(0,str(source))
    from photo_plane import CAMERAS
    from ionic_portico import STONE
    from coffered_soffit import GLASS
    tools=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    faces,idx,names,identity=tools['load_triangles'](mesh)
    camera=CAMERAS['close'];inv=np.linalg.inv(camera[:,:3]);eye=-inv@camera[:,3]
    vertices=faces.reshape(-1,3);q=vertices@camera[:,:3].T+camera[:,3]
    projected=(q[:,:2]/q[:,2,None]).reshape(-1,3,2)
    lo=projected.min(axis=1)-.001;hi=projected.max(axis=1)+.001
    normal=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
    appearances=tools['material_appearance'](mesh)['materials']
    double=np.array([appearances[s]['doubleSided']for s in names])[idx]
    bin_ids={}
    def hit(uv):
        p=np.asarray(uv)
        cell=tuple(np.floor(p/32.).astype(int))
        if cell not in bin_ids:
            low=np.asarray(cell)*32;high=low+32
            bin_ids[cell]=np.flatnonzero(np.all(lo<=high,axis=1)&np.all(hi>=low,axis=1))
        ids=bin_ids[cell];d=inv@np.r_[p,1.];d/=np.linalg.norm(d)
        keep=np.all(lo[ids]<=p,axis=1)&np.all(hi[ids]>=p,axis=1)&(double[ids]|(normal[ids]@d<-1e-11))
        ids=ids[keep]
        if not len(ids):return None,None
        i,t,xyz=tools['first_hit'](faces[ids],eye,d)
        return (names[idx[ids[i]]],xyz) if np.isfinite(t) else (None,None)
    traced=json.loads((source.parent/'measurements/ionic-front-traces.json').read_bytes())
    visible_face=Polygon(traced["front_silhouette"])
    volutes=[]
    for name,curve in traced["scroll_crests"].items():
        curve=np.array(curve);sides=[]
        for i in np.rint(np.linspace(.13,.86,17)*(len(curve)-1)).astype(int):
            p=curve[i];t=curve[i+2]-curve[i-2];n=np.array([-t[1],t[0]])/np.linalg.norm(t)
            centre=hit(p);edges=[hit(p+n*d)for d in [-2.9,2.9]]
            offsets=[round(float(r[1][1]-centre[1][1]),5) if r[0]==centre[0]==STONE else None for r in edges]
            edge_positions=[p-n*2.9,p+n*2.9]
            in_face=[visible_face.covers(Point(q))for q in edge_positions]
            # The outer edge of the photographed upper right spiral runs along
            # the silhouette. Its outside control should see a return or the
            # backing; its inside control must still fall below the raised stone.
            checks=[(off is not None and off>.003) if inside else
                    (part!=STONE or (off is not None and off>.003))
                    for (part,_),off,inside in zip(edges,offsets,in_face)]
            sides.append(dict(edge_in_photographed_silhouette=in_face,adjacent_materials=[r[0]for r in edges],crest_px=p.round(2).tolist(),adjacent_px=[(p-n*2.9).round(2).tolist(),(p+n*2.9).round(2).tolist()],
                              crest_surface=centre[0],crest_y_m=round(float(centre[1][1]),5) if centre[1] is not None else None,
                              edge_relief_m=offsets,passed=all(checks)))
        volutes.append(dict(feature=name,sections=sides))
    # In the original image each shallow, pale cover is visible between an upper
    # horizontal fillet and the rear beam. Require the shell both across its face
    # and at the lower edge, and a different material just beyond the bottom.
    domes=[]
    for x,y,left,right in [(854,1133,821,886),(1188,1125,1156,1220),(1514,1117,1482,1545)]:
        samples=[]
        for frac,down,inside in [(0.,5,True),(-.54,7,True),(.54,7,True),(0.,12,True),(0.,27,False),(-1.19,9,False),(1.19,9,False)]:
            p=[x+frac*(right-left)/2.,y+down];mat,xyz=hit(p)
            samples.append(dict(px=p,expected_cover=inside,actual_material=mat,passed=bool(mat) and ((mat==GLASS)==inside)))
        domes.append(dict(centre_px=[x,y],samples=samples))
    shafts=json.loads((source.parent/'measurements/fluted-shafts.json').read_bytes())
    x,y,r=shafts["columns"][3]["shaft_xyr_m"]
    axes=json.loads((source.parent/'measurements/north-portico-axes.json').read_bytes())["axes"][3]
    base,neck=[axes["z_and_pixels"][key]["z_m"] for key in ("base","neck")]
    def flute_point(u,v):
        mat,xyz=hit([u,v])
        if mat!=STONE:return None
        t=(xyz[2]-base)/(neck-base)
        outer=r*(1.+.085*(1.-t)+.021*np.sin(np.pi*t))
        return float(outer-np.hypot(xyz[0]-x,xyz[1]-y))
    scans=[]
    for row in shafts['heldout_fourth_shaft']:
        v=row['v_px'];us=np.asarray(row['observed_troughs_px'])
        valleys=[]
        for centre in us:
            stamped=[(u,d)for u in np.arange(centre-2.5,centre+2.51,.5) if (d:=flute_point(u,v)) is not None]
            best=max(stamped,key=lambda s:s[1]) if stamped else (None,None)
            valleys.append(dict(source_u=float(centre),observed_mesh_u=best[0],recess_m=best[1],
                                passed=best[1] is not None and best[1]>.0075))
        dividers=[]
        for i,(before,after) in enumerate(zip(us[:-1],us[1:])):
            stamped=[(u,d)for u in np.linspace(before+.25*(after-before),after-.25*(after-before),12)
                     if (d:=flute_point(u,v)) is not None]
            best=min(stamped,key=lambda s:s[1]) if stamped else (None,None)
            adjacent=[v["recess_m"]for v in valleys[i:i+2] if v["recess_m"] is not None]
            relief=min(adjacent)-best[1] if best[1] is not None and len(adjacent)==2 else None
            dividers.append(dict(source_interval_u=[before,after],observed_mesh_u=best[0],
                                 adjoining_recess_difference_m=relief,passed=relief is not None and relief>.004))
        scans.append(dict(photo_v=v,channel_troughs=valleys,separating_fillets=dividers))
    return dict(mesh=identity,volutes=volutes,covers=domes,shaft_sections=scans)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mesh','project','source','output'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();r=check(a.mesh,a.project,a.source);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
    print([(v['feature'],sum(s['passed']for s in v['sections']),[(s['crest_px'],s['edge_relief_m']) for s in v['sections'] if not s['passed']])for v in r['volutes']])
    print([[s['actual_material']for s in v['samples']]for v in r['covers']])
    print("shaft",sum(s["passed"] for row in r["shaft_sections"] for s in row["channel_troughs"]),"/32",
          sum(s["passed"] for row in r["shaft_sections"] for s in row["separating_fillets"]),"/24")
    passed=[s['passed'] for row in r['volutes'] for s in row['sections']]
    passed.extend(s['passed'] for row in r['covers'] for s in row['samples'])
    passed.extend(s['passed'] for row in r['shaft_sections'] for key in ['channel_troughs','separating_fillets'] for s in row[key])
    if not all(passed):raise SystemExit(1)
