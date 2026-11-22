from pathlib import Path
import json,numpy as np
S=Path(__file__).resolve().parent
cam=json.loads((S/'southern-neighbouring-cameras.json').read_bytes());P={k:np.array(v['local_xyz_to_image'])for k,v in cam.items()}
def tri(a,pa,b,pb):
 def eq(p,u,v):return [p[0]-u*p[2],p[1]-v*p[2]]
 _,_,vt=np.linalg.svd(np.array(eq(P[a],*pa)+eq(P[b],*pb)));x=vt[-1]/vt[-1,-1]
 def error(p,uv):
  q=p@x;return float(np.linalg.norm(q[:2]/q[2]-uv))
 return x[:3].round(3).tolist(),[round(error(P[a],pa),1),round(error(P[b],pb),1)]
def inverse(n,u,v,val,axis):
 m=P[n];keep=[0,2,3]if axis==1 else[1,2,3];h=m[:,keep].copy();h[:,2]+=val*m[:,axis];vv=np.linalg.solve(h,[u,v,1]);return np.round(vv[:2]/vv[2],3).tolist()
# Four corners read clockwise from image top left, with upper and lower leaf divisions checked separately.
fields={
 'S-pair-A3':('south',[(358,284),(404,282),(402,339),(355,341)],[(322,311),(365,322),(358,370),(316,361)]),
 'S-pair-B3':('south',[(452,279),(492,277),(494,336),(451,337)],[(414,333),(447,344),(442,387),(408,379)]),
 'S-pair-A2':('south',[(347,442),(392,442),(390,527),(340,528)],[(310,464),(355,472),(353,545),(304,535)]),
 'S-pair-B2':('south',[(449,440),(495,438),(494,526),(448,526)],[(407,481),(443,487),(441,558),(403,551)]),
 'S-near3':('south',[(639,342),(679,340),(682,408),(643,408)],[(549,421),(578,430),(581,473),(551,469)]),
 'S-near2':('south',[(643,518),(680,516),(682,557),(643,559)],[(555,566),(580,569),(580,606),(553,602)]),
 'N-pair-A3':('north',[(372,267),(412,279),(413,341),(372,335)],[(472,306),(494,312),(493,353),(472,348)]),
 'N-pair-B3':('north',[(449,289),(487,300),(486,355),(449,347)],[(515,320),(535,324),(535,369),(513,362)]),
 'N-pair-A2':('north',[(371,420),(406,426),(405,495),(370,490)],[(469,416),(493,422),(492,469),(467,462)]),
 'N-pair-B2':('north',[(452,431),(485,435),(484,503),(451,500)],[(511,426),(533,433),(532,485),(510,479)]),
 'N-next3':('north',[(570,374),(595,380),(597,423),(573,419)],[(582,383),(596,388),(597,422),(583,417)]),
 'N-next2':('north',[(572,507),(597,509),(596,553),(574,552)],[(582,487),(601,490),(600,517),(584,516)]),
 'N-return3':('north',[(248,308),(282,293),(280,344),(247,354)],[(336,324),(377,313),(377,355),(336,365)]),
 'N-return2':('north',[(226,447),(269,430),(267,501),(222,517)],[(333,429),(379,420),(377,481),(328,495)]),
}

def fit_facade(ids, side, ref):
    from scipy.optimize import least_squares
    # The short return runs towards decreasing local Y from left to right on both plates.
    reverse = side == 'north-lane-return'
    along, depth = (1,0) if reverse else (0,1)
    source = []
    for key in ids:
        face, first, second = fields[key]
        cams = [face+'-block-n21',face+'-block-s21']
        xyz = np.array([tri(cams[0],a,cams[1],b)[0] for a,b in zip(first,second)])
        source.append((key,cams,np.array([first,second]),xyz))
    depth0 = np.median(np.concatenate([r[3][:,depth] for r in source]))
    init = [depth0,0.]
    for _, _, _, xyz in source:
        left,right = np.mean(xyz[[0,3],along]),np.mean(xyz[[1,2],along])
        init.extend([min(left,right),max(left,right),np.mean(xyz[2:,2]),np.mean(xyz[:2,2])])
    def projected(params,i):
        _,cams,_,_ = source[i]
        low,high,b,t = params[2+4*i:6+4*i]
        left,right = (high,low) if reverse else (low,high)
        xyz=[]
        for u,z in ((left,t),(right,t),(right,b),(left,b)):
            d=params[0]+params[1]*(u-ref)
            xyz.append([d,u,z,1] if reverse else [u,d,z,1])
        out=[]
        for key in cams:
            p=(P[key]@np.array(xyz).T).T
            out.append(p[:,:2]/p[:,2,None])
        return np.array(out)
    def residual(params):
        return np.concatenate([(projected(params,i)-r[2]).ravel() for i,r in enumerate(source)])
    fit=least_squares(residual,init,loss='soft_l1',f_scale=3).x
    data=[]
    for i,(key,cams,uv,xyz) in enumerate(source):
        errs=np.linalg.norm(projected(fit,i)-uv,axis=2)
        l,r,b,t=fit[2+4*i:6+4*i]
        modern=key.startswith('S-')
        pair='-pair-' in key
        # Fractions run upwards. The southern upper paired leaves have no horizontal division.
        if modern:
            cuts=[.74] if pair and key.endswith('2') else []
        else:
            cuts=[.25,.50,.75] if key not in ('N-next2','N-next3') else ([.25,.5,.75] if key.endswith('2') else [.5])
        opts=dict(id=key,facade=side,u0=round(l,4),u1=round(r,4),z0=round(b,4),z1=round(t,4),
                  frame='pale' if modern else 'dark',horizontal_divisions=cuts,
                  vertical_divisions=[.5],
                  upper_undivided=modern and bool(cuts),front_pair=pair,
                  mean_projection_error_px=round(float(errs.mean()),2),
                  max_projection_error_px=round(float(errs.max()),2),
                  observed=dict(zip(cams,uv.tolist())))
        if key=='S-near2': opts['limit']='The storefront fascia masks the sill. Only the visible glazed height is measured.'
        if key=='N-next2': opts['limit']='Shopfront fascia reaches the sill. The bottom is a visible limit.'
        if key=='N-return2': opts['limit']='A projecting rail and open dark elements overlap the lower opening. Hinge angle is unresolved.'
        if key=='N-next3': opts['limit']='Tree branches cross the centre; the weaker glazing bars are only partially resolved.'
        data.append(opts)
    return dict(axis='Y' if reverse else 'X',local_reference=ref,
                frame_plane=round(fit[0],5),depth_slope=round(fit[1],5),
                error_rms_px=round(float(np.sqrt(np.mean(residual(fit)**2))),2)),data

def main():
    surfaces={}
    openings=[]
    for side,keys,ref in [('south-front',[k for k in fields if k.startswith('S-')],-6),
                          ('north-front',[k for k in fields if k.startswith('N-') and 'return' not in k],7),
                          ('north-lane-return',[k for k in fields if 'return' in k],3)]:
        surfaces[side],group=fit_facade(keys,side,ref)
        openings.extend(group)
    camfile=S/'southern-neighbouring-cameras.json'
    import hashlib
    out=dict(units='metres',calibration=camfile.name,camera_sha256=hashlib.sha256(camfile.read_bytes()).hexdigest(),
             method='Four corners per opening in two February 2021 native winter views. Fit planes and rectangles jointly with a 3 px robust loss. Coordinates are measured at the front of the fixed window frame. Return width follows Y. Each observation runs top left, top right, bottom right, bottom left in image pixels.',
             remarks='The photographs resolve frame colour, mullions and glazing patterns more clearly than hinge hardware. Southern lower paired windows have one undivided high transom and two pale lower lights. The northern late-summer 2017 high resolution view independently distinguishes pale southern casements and dark northern grilles.',
             surfaces=surfaces,openings=openings)
    from refit_north_windows import update_book
    from refit_south_return import append_return
    from refit_inner_windows import append_inner
    out=append_inner(append_return(update_book(out)))
    dest=S/'street-window-openings.json'
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(surfaces)
    for p in out['openings']: print(p['id'],p['u0'],p['u1'],p['z0'],p['z1'],p['mean_projection_error_px'],p['max_projection_error_px'])
if __name__=='__main__':main()
