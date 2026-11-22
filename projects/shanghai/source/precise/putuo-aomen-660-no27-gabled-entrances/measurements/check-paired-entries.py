"""Check left and right door components, numbered plaque and independently read arch edges in object space."""
from pathlib import Path
from hashlib import sha256
import argparse,json,runpy,sys
import numpy as np

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('report',type=Path)
    ap.add_argument('--project',type=Path);ap.add_argument('--mesh',action='append',default=[])
    args=ap.parse_args();w=Path(__file__).resolve().parents[1]
    project=args.project or next(p for p in w.parents if (p/'tools/package_architectural_model.py').is_file())
    sys.path[:0]=[str(project/'tools'),str(w/'source')]
    import package_architectural_model
    from photo_architecture import Builder
    import paired_entries as mod
    lib=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    info=mod.DATA
    def cast(tri,labels,u,v):
        px,pz=(u-267.)*.018,(358.-v)*.018
        floor=tri.min(axis=1);ceil=tri.max(axis=1)
        select=np.flatnonzero((floor[:,0]<=px)&(ceil[:,0]>=px)&(floor[:,2]<=pz)&(ceil[:,2]>=pz))
        if not len(select):return None,None
        index,t,*_=lib['first_hit'](tri[select],np.array([px,-1.5,pz]),np.array([0.,1.,0.]))
        if not np.isfinite(t):return None,None
        return str(labels[select[index]]),round(float(t)-1.5,6)
    def examine(tri,labels,source):
        probes=[('left shut leaf',187.0,344.0,[mod.DOOR]),('left sash glass',178.3,285,[mod.NARROW]),
                ('left right-leaf upper field',209,286,[mod.PANEL]),('left lower field',200,336,[mod.PANEL]),
                ('right exposed stroke of open door',308,301,[mod.DOOR]),('right unobstructed passage',329,300,[mod.DARK]),
                ('right retained shut leaf',356,312,[mod.PANEL]),('right jamb',378,271.8,list(mod.CLAY)+[mod.MORTAR]),
                ('left upright soldier',210,255.4,list(mod.CLAY)+[mod.MORTAR]),('right upright soldier',335,252,list(mod.CLAY)+[mod.MORTAR]),
                ('left projection',202,247.2,[mod.LEDGE,mod.EDGE]),('right projection',334,240.8,[mod.LEDGE,mod.EDGE]),
                ('left fan pane',198,222,[mod.GLASS]),('right fan pane',333,216,[mod.GLASS]),
                ('left stone crown',198,207.5,[mod.WHITE]),('right stone crown',332,201,[mod.WHITE]),
                ('plate ground',398.3,261.8,[mod.PLATE]),('plate 7 top',396.06,258.16,[mod.LETTER]),
                ('left threshold',184,357.7,[mod.STONE]),('right threshold',327,357.6,[mod.STONE])]
        out=[]
        for label,u,v,wanted in probes:
            name,y=cast(tri,labels,u,v);out.append(dict(label=label,u=u,v=v,expected=wanted,actual=name,y=y,matched=name in wanted))
        # Compare the independently observed edges against cross sections of the
        # actual tessellated lime strip. Intersections use only its exposed front bevels.
        subset=tri[np.isin(labels,[mod.WHITE,mod.BEVEL])]; uv=np.stack((subset[:,:,0]/.018+267,358.-subset[:,:,2]/.018),axis=2)
        face_ok=np.max(subset[:,:,1],axis=1)<=-.022
        uv=uv[face_ok]
        edges={}
        for triangle in uv:
            for i in range(3):
                a,b=triangle[i],triangle[(i+1)%3]
                k=tuple(sorted((tuple(np.round(a,4)),tuple(np.round(b,4)))))
                edges[k]=edges.get(k,0)+1
        rows=[]
        for side,arches in info['arches'].items():
            for edge,spec in arches.items():
                cx,cy,rx,rz,slope=spec['ellipse']
                for obs in spec['held_out']:
                    angle=np.radians(obs['theta']);vec=np.array([np.cos(angle),-np.sin(angle)])
                    target=np.array([obs['u'],obs['v']]);hits=[]
                    # Cast a 2D line normal to the photographed edge; keep only
                    # the external perimeter edges instead of the triangulation diagonals.
                    for (p,q),count in edges.items():
                        if count!=1:continue
                        p=np.array(p);d=np.array(q)-p;mat=np.column_stack([vec,-d])
                        if abs(np.linalg.det(mat))<1.e-8:continue
                        dist,mu=np.linalg.solve(mat,p-target)
                        if 0<=mu<=1 and abs(dist)<6:hits.append(float(dist))
                    resid=min(hits,key=abs) if hits else None
                    rows.append(dict(side=side,edge=edge,angle=obs['theta'],photo=[obs['u'],obs['v']],signed_residual_px=resid,contrast=obs['contrast']))
        visible=[abs(row['signed_residual_px']) for row in rows if row['signed_residual_px'] is not None]
        return dict(source=source,controls=out,edges=rows,edge_matches=len(visible),edge_median_px=float(np.median(visible)),edge_p95_px=float(np.percentile(visible,95)),edge_max_px=max(visible))
    res={}
    if not args.mesh:
        for flag in [False,True]:
            b=Builder(mod.PALETTE);mod.add_entries(b,flag);tri=[];labels=[]
            for component in b.parts:
                shape=np.asarray(component['vertices'])[np.asarray(component['triangles'])];tri.extend(shape);labels.extend([component['material']]*len(shape))
            res['lod' if flag else 'full']=examine(np.array(tri),np.array(labels),dict(parts=len(b.parts),triangles=len(tri)))
    for s in args.mesh:
        role,f=s.split('=',1);tri,ids,names,rec=lib['load_triangles'](Path(f));rec.pop('file',None)
        res[role]=examine(tri,np.asarray(names)[ids],rec)
    data=dict(photo_sha256=info['photo_sha256'],helper_sha256=sha256((w/'source/paired_entries.py').read_bytes()).hexdigest(),survey_sha256=sha256((w/'measurements/paired-entries.json').read_bytes()).hexdigest(),checks=res)
    data['passed']=all(all(c['matched'] for c in r['controls']) and r['edge_matches']==36 and r['edge_p95_px']<3.0 and r['edge_max_px']<4.5 for r in res.values())
    args.report.write_text(json.dumps(data,indent=2)+'\n')
    for role,r in res.items():
        print(role,r['source'],[(q['label'],q['actual'],q['y']) for q in r['controls'] if not q['matched']],r['edge_matches'],r['edge_median_px'],r['edge_p95_px'],r['edge_max_px'])
    if not data['passed']:raise AssertionError('Door materials, openings, house number or measured arches changed')
if __name__=='__main__':main()
