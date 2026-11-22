"""Measure the southern window jambs, shop door swings and return walls in the architect's plans."""
from hashlib import sha256
from pathlib import Path
import argparse,json
import numpy as np
from PIL import Image

NAMES=('W5','W4','W3','W2','W1','Cw','Cc','Ce','E1','E2','E3','E4','E5')
TRACES={32:[[108,553],[161,573],[209,587],[257,597],[306,608],[355,616],[397,622],[438,627],[489,633],[537,638],[588,644],[638,647],[688,649]],
        29:[[176,613],[221,628],[268,642],[315,654],[363,664],[411,671],[449,677],[487,683],[535,687],[580,692],[629,697],[679,700],[723,703]]}
SWINGS=[[197,210],[241,254],[286,299],[331,344],[377,389],[503,515],[548,561],[594,607],[640,653],[686,699]]
PLAN32_EDGES=[[127,153],[173,200],[220,247],[268,295],[315,343],[372,383],[390,401],[408,419],[448,476],[496,525],[545,573],[593,621],[642,670]]
def norm(v,trace):
    xy=np.asarray(trace)
    length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    return np.interp(v,xy[:,0],length)/length[-1]
def scan(im,trace,offsets,cutoff):
    x=np.arange(im.shape[1]);c=np.asarray(trace);y=np.interp(x,*c.T)
    rows=[im[np.rint(y+d).astype(int),x] for d in offsets]
    return np.maximum(0,cutoff-np.stack(rows).astype(float)).sum(axis=0)
def bounds32(im):
    profile=scan(im,TRACES[32],range(-4,5),200)
    bounds=[]
    for threshold in (155,185,220):
        # In plan32 masonry is continuous dark ink, windows are drawn with thin parallel lines.
        known=TRACES[32];left,right=known[0][0],known[-1][0]
        level=profile[left:right+1]>threshold
        runs=np.where(np.diff(np.r_[False,level,False]))[0].reshape(-1,2)+left
        piers=np.array([(a,b)for a,b in runs if b-a>=5])
        pairs=np.column_stack((piers[:-1,1],piers[1:,0]))
        assert pairs.shape==(13,2) and np.max(abs(pairs-np.asarray(PLAN32_EDGES)))<=2
        bounds.append(pairs)
    return np.median(bounds,axis=0),np.stack(bounds)
def return_xy(pts,outline,chord):
    start,end=np.array(outline[0],float),np.array(outline[-1],float)
    dx=end-start;unit=dx/np.linalg.norm(dx);inward=np.array([unit[1],-unit[0]])
    origin=(start+end)*.5;s=chord/np.linalg.norm(dx)
    xy=np.array(pts,float)-origin
    return np.round(np.stack([xy@unit,xy@inward],axis=1)*s,3).tolist()
def rounded(v):return np.round(v,6).tolist()
def write(output,source,prior,chord):
    p32=source/'pic-32.jpg';p29=source/'pic-29.jpg'
    im32=np.array(Image.open(p32).convert('L'));im29=np.array(Image.open(p29).convert('L'))
    assert list(im32.shape)==[847,816] and list(im29.shape)==[866,828]
    pp,all_edges=bounds32(im32)
    frac32=norm(pp,TRACES[32]);photo=json.loads(prior.read_bytes())
    previous={o['key']:o for o in photo['openings']}
    old=np.array([[previous[f'{n}-F4'][k]for k in ('u_west','u_east')]for n in NAMES]);delta=frac32-old
    ink29=scan(im29,TRACES[29],range(4,9),225)
    f1=np.array(photo['ground_check']['within_bay_normalized'])
    ground={};details=[]
    for (left,right),name in zip(SWINGS,NAMES[:5]+NAMES[-5:]):
        # The darkest pair of swing strokes 4–8 original pixels outboard of the
        # opening makes the two-leaf shop door visible even under the flow arrow.
        assert all(ink29[x]==max(ink29[x-2:x+3]) and ink29[x]>200 for x in (left,right))
        xx=np.array([left,right],float);tr=np.array(TRACES[29],float)
        slope=np.interp(xx,tr[:,0],np.gradient(tr[:,1],tr[:,0]))
        support=xx+6*slope/(1+slope*slope)
        jamb=norm(support,TRACES[29]);span=(jamb[1]-jamb[0])/(f1[3]-f1[2])
        envelope=jamb[0]-span*f1[2]
        ground[name]=(envelope+span*f1).reshape(3,2)
        details.append(dict(bay=name,darkest_plan29_swing_marks_px=[left,right],projected_onto_masonry_line_x=rounded(support),central_clear=rounded(jamb),estimated_full_assembly=rounded([envelope,envelope+span])))
    rows=[]
    for i,name in enumerate(NAMES):
        for level in (4,3,2):
            key=f'{name}-F{level}';a,b=frac32[i]
            rows.append(dict(key=key,bay=name,level=level,family=previous[key]['family'],u_west=round(a,6),u_east=round(b,6),basis='Standard floor masonry-to-thin glazing transition in plan 32, verified on the facade photographs at levels two through four.'))
        for j,(a,b) in enumerate(ground.get(name,[])):
            suffix=('w','m','e')[j];key=f'{name}-F1-{suffix}'
            rows.append(dict(key=key,bay=name,level=1,family=previous[key]['family'],u_west=round(a,6),u_east=round(b,6),basis='10 observed two-leaf shop openings in plan 29. Side lights and stone splits transferred from the completed E1 shop photograph.'))
    assert len(rows)==69
    turns32={'west':[[108,553],[137,296],[218,296],[218,210]],'east':[[688,649],[686,296],[604,296],[604,210]]}
    turns29={'west':[[176,613],[204,370],[280,370],[280,286]],'east':[[723,703],[722,370],[644,370],[644,286]]}
    returns={}
    for key in ('west','east'):
        pts=turns32[key];pp29=turns29[key]
        lengths=np.linalg.norm(np.diff(pts,axis=0),axis=1)*chord/np.linalg.norm(np.subtract(TRACES[32][-1],TRACES[32][0]))
        returns[key]=dict(standard_plan_px=pts,ground_plan_px=pp29,cartesian_standard_relative_to_chord_midpoint=return_xy(pts,TRACES[32],chord),cartesian_ground_relative_to_chord_midpoint=return_xy(pp29,TRACES[29],chord),estimated_metres_along_each_straight_segment=rounded(lengths))
    front37=[[127,525],[741,627]]
    roof37={'west':[157,251],'east':[739,252]}
    roof_check={}
    for side in ('west','east'):
        end=return_xy([roof37[side]],front37,chord)[0]
        plan=returns[side]['cartesian_standard_relative_to_chord_midpoint'][1]
        displacement=np.subtract(end,plan)
        roof_check[side]=dict(front_corner_37=front37[0 if side=='west' else 1],
            plan37_back_corner_pixel=roof37[side],plan37_corner_chord_m=end,
            roof_minus_standard_plan_m=rounded(displacement),
            corner_gap_m=round(float(np.linalg.norm(displacement)),4))
    out=dict(reference='Guang Er Warehouse renovation architect’s floor-1 and typical-floor circulation drawings, reproduced in the 2026 studio publication.',photos={str(n):dict(filename=f'pic-{n}.jpg',sha256=sha256((source/f'pic-{n}.jpg').read_bytes()).hexdigest(),size=[int(v)for v in Image.open(source/f'pic-{n}.jpg').size])for n in [29,32,37]},
        coordinate='Continuous plan arc, measured west to east along the actual drawn southern wall. Both plans measured independently. It is normalized from 0 to 1. Local plan corners are given separately around the *chord* midpoint with north/inward positive Y.',
        exterior_curves=TRACES,reference_chord_m=chord,
        typical_floor=dict(row_groups=NAMES,median_jamb_pixels=pp.tolist(),dark_threshold_repeats=all_edges.tolist(),full_window_spans=rounded(frac32),max_jamb_spread_px=int(np.ptp(all_edges,axis=0).max()),three_central_apertures_including_two_masonry_mullions=rounded([frac32[5,0],frac32[7,1]]),central_group_fraction=round(float(frac32[7,1]-frac32[5,0]),6)),
        ground_floor=dict(swing_check=details,within_bay_glass_and_pier_from_built_photo=rounded(f1),note='The contemporary shop glazing may change behind the thick stone divisions. The typical floor supplies no evidence for ground-level panes. In plan 29 the two swing leaves and their clear width can be checked independently at all ten bays.'),
        photo_comparison=dict(earlier_table=prior.name,earlier_sha256=sha256(prior.read_bytes()).hexdigest(),jamb_displacements_plan_minus_photographic_table=rounded(delta),median_absolute_fraction=round(float(np.median(abs(delta))),6),maximum_absolute_fraction=round(float(np.max(abs(delta))),6)),
        gable_returns=returns,west_ground_limit='The thinner ground-floor line at x234 px forms a service or entrance zone inboard of the drawn west side. The registered upper mass and heavy ground-level partition turn near x280 px. The upper plan alone does not establish full ground-level enclosure.',roof_corner_validation=roof_check,scope='Sidewall lines and the first complete northern recess are visible in the architectural plans. Relative ground/standard corner disagreement is recorded to support a cut-off, not to prove the construction of an occluded annex.',openings=rows)
    output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('studio_originals',type=Path);p.add_argument('output',type=Path);p.add_argument('--chord',type=float,default=59.369)
 a=p.parse_args();out=write(a.output,a.studio_originals,Path(__file__).with_name('south-window-normalized-layout.json'),a.chord)
 print(out['typical_floor']['full_window_spans'],out['gable_returns'])
