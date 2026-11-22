"""Compare actual historic montage and restored photographs without equating perspective pixels and metres."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

# The unrectified x intervals are observed jamb lines in the stated original full frames.
NAMES=('W5','W4','W3','W2','W1','Cw','Cc','Ce','E1','E2','E3','E4','E5')
historic=np.array([[76,116],[142,184],[210,250],[272,313],[337,377],[415,430],[437,453],[460,476],
                   [514,555],[579,619],[641,682],[707,749],[775,816]],float)
pre=np.array([[26,58],[80,115],[140,180],[204,244],[271,312],[352,371],[378,397],[404,423],
              [462,504],[531,573],[599,640],[664,704],[728,766]],float)
design=np.array([[55,83],[103,133],[157,191],[217,257],[286,327],[369,389],[396,416],[423,442],
                 [485,529],[558,602],[631,677],[705,748],[776,818]],float)
air=np.array([[321,330],[341,353],[365,381],[392,409],[422,440],[461,469],[474,482],[486,494],
              [518,539],[557,581],[598,623],[643,669],[689,719]],float)
# The current front photograph covers the central five unobscured observations.
central_ix=np.array([4,5,6,7,8])
front=np.array([[315,395],[473,510],[525,561],[575,612],[690,770]],float)
oldfloor1=np.array([[75,116],[142,184],[209,250],[271,313],[336,377],[0,0],[0,0],[0,0],
                    [514,555],[579,620],[641,682],[707,749],[775,816]],float)
def fit(source,target):
    # A smooth near-affine quadratic corrects residual foreshortening on the
    # bowed full front. Calibrate on bay centres, reserve *both* jambs for width checks.
    return np.polynomial.Polynomial.fit(source,target,3)
def rounded(seq):return np.round(seq,6).tolist()
def main(dest):
    reference=historic.mean(axis=1)
    map_pre=fit(pre.mean(axis=1),reference)
    left=float(map_pre(4));right=float(map_pre(791))
    norm=lambda x:(x-left)/(right-left)
    records={};estimates=[]
    for key,source,ix in [('pic-14',pre,np.arange(13)),('civic-3-0',air,np.arange(13)),('civic-3-4',front,central_ix),('pic-15',design,np.arange(13))]:
        x=source.mean(axis=1);y=reference[ix]
        poly=fit(x,y)
        ycheck=[]
        for i in range(len(x)):
            keep=np.arange(len(x))!=i
            # A five-point frontal crop is tested by its three inner holdouts.
            if len(x)==5 and i in (0,4):continue
            ycheck.append(float(norm(fit(x[keep],y[keep])(x[i]))-norm(y[i])))
        xmin,xmax=source.min(),source.max()
        assert np.all(poly.deriv()(np.linspace(xmin,xmax,100))>0)
        remap=norm(poly(source))
        records[key]=dict(names=[NAMES[i]for i in ix],jambs_original_px=source.astype(int).tolist(),
                          full_frame_x_ranges_per_role='Original upper-floor x extents. At distant western end in the current aerial each jamb has 1–2 px read uncertainty.',
                          mapped_jambs=rounded(remap),max_held_out_bay_axis_error_fraction=round(max(abs(v)for v in ycheck),5),
                          cubic_coefficients_image_to_montage_ascending=poly.convert().coef.tolist())
        if key!='pic-15':estimates.append((ix,remap))
    # Current built frames are checked with two different real viewpoints. The
    # architects' proposed rendering is recorded only as a separate design comparison.
    fitted=[]
    for i,(l,r) in enumerate(historic):
        a=[norm(np.array([l,r]))]
        for ix,mp in estimates:
            if i in ix:a.append(mp[list(ix).index(i)])
        fitted.append(np.median(a,axis=0))
    fitted=np.array(fitted)
    # The building verticals are kept near vertical by the current oblique image.
    # Match the upper jamb positions of the five adjacent openings to the derived
    # facade coordinate, then transfer the six ground-level jambs by that map.
    oblique=np.array([[186,287],[389,437],[462,519],[551,611],[759,949]],float)
    true=fitted[central_ix].flatten()
    measured=oblique.flatten()
    def prediction(p,x):return (p[0]+p[1]*x)/(1+p[2]*x)
    pars=least_squares(lambda p:prediction(p,measured)-true,[.26,.0004,0]).x
    groundpx=np.array([759,790,807,899,916,950])
    coord=prediction(pars,groundpx)
    f1=(coord-coord[0])/(coord[-1]-coord[0])
    rows=[]
    for i,(a,b)in enumerate(fitted):
        name=NAMES[i];central=name.startswith('C')
        for level in [4,3,2]:
            family=(('central' if central else 'wide')+('-second' if level==2 else '-upper'))
            rows.append(dict(key=f'{name}-F{level}',bay=name,level=level,family=family,u_west=round(a,6),u_east=round(b,6),support='Upper steel opening on the same jamb axes in the architect’s two photographed stages. Three near-centre levels visually cross-checked at current close range.'))
        if central:continue
        # Each historic wide storefront envelope corresponds to its upper masonry
        # opening. Dark ground bands are also measurable at y=247 and y=275 in pic-13.
        envelope=np.array([a,b])+norm(oldfloor1[i])-norm(historic[i])
        # On the contemporary pic-17 the first east storefront sides are nearly
        # vertical. Correct their local horizontal foreshortening against the close
        # central/right bays on the same current photograph. A small sensitivity
        # bound covers interpreting the branches at the left and right perimeter.
        for suffix,x0,x1,fam in [('w',f1[0],f1[1],'ground-side'),('m',f1[2],f1[3],'ground-mid'),('e',f1[4],f1[5],'ground-side')]:
            rows.append(dict(key=f'{name}-F1-{suffix}',bay=name,level=1,family=fam,
                             u_west=round(envelope[0]+x0*np.diff(envelope)[0],6),u_east=round(envelope[0]+x1*np.diff(envelope)[0],6),
                             support='Current built E1 clear vs masonry divisions; repeated distribution from the original entrance strips. Full contemporary street fronts are partly screened by planting and shop signs.'))
    result=dict(coordinate='Unitless distance along the continuous southern street frontage, west edge 0, east edge 1. Apply to the surveyed total run and local curved wall rather than uncorrected photo x.',
        convention='W5 and E5 are the outer western and eastern bays; Cw/Cc/Ce are three separate narrow openings over the through passage.',
        indexed_windows=len(rows),source_full_frame_px={'pic-13':[831,317],'pic-14':[802,367],'pic-15':[865,383],'civic-3-0':[1080,720],'civic-3-4':[1080,810],'pic-17':[1080,1620]},
        historic_montage=dict(upper_jambs_original_px=historic.astype(int).tolist(),ground_envelopes_px=oldfloor1.astype(int).tolist(),ground_horizontal_scan_y=[247,275],
           visible_west_edge_px=50,normalized_endpoint_estimates_in_montage=[round(left,2),round(right,2)],reason='The historic montage crops the extreme east margin. Both endpoints are transferred from the complete pre-conservation photo, in which the west/east wall boundaries lie at x=4/791.'),
        sources=records,after_construction_read='civic-3-0 and civic-3-4 are built photographs. Pic-14 is the previous facade. Pic-13 synthesizes historic photographs into a frontal montage. Pic-15 is a proposed design only. Citing all five distinguishes the apparent spacings, including the narrower-looking west end in pic-15.',
        ground_check=dict(photo='pic-17',pixels_at_glazing_height=[759,790,807,899,916,950],within_bay_normalized=rounded(f1),upper_jambs_for_local_oblique_correction=oblique.astype(int).tolist(),fitted_projective_function=list(pars),max_upper_jamb_residual_fraction=round(float(np.max(np.abs(prediction(pars,measured)-true))),6),uncertainty_of_internal_pier_jambs_as_bay_fraction=.025,
                          history_example=dict(photo='pic-13',scan_y=275,west_near_centre_dark_intervals=[[336,345],[347,366],[368,377]]),central_passage='No ground glazing in the Cw/Cc/Ce openings. The through passage and its sign are separate construction.'),
        uncertainty='Near centre, normalized across-image jamb spreads can be checked below. Overall phase of the historic montage and the cropped eastern margin cause a wall-end/curve uncertainty of roughly 0.004–0.010 of full frontage. Oblique views constrain occluded bay widths collectively but cannot recover unseen shop fittings. A fully georeferenced site fit supersedes absolute translation and scale.',
        upper_jamb_spread_across_actual_sources=rounded(np.ptp(np.stack([norm(historic),np.asarray(records['pic-14']['mapped_jambs']),np.asarray(records['civic-3-0']['mapped_jambs'])]),axis=0)),
        openings=rows)
    assert len(rows)==69 and all(0<a['u_west']<a['u_east']<1 for a in rows)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result
if __name__=='__main__':
 import sys
 result=main(Path(sys.argv[1]))
 print(result['historic_montage']['normalized_endpoint_estimates_in_montage'])
 print([(r['key'],r['u_west'],r['u_east']) for r in result['openings'] if r['level']==4])
