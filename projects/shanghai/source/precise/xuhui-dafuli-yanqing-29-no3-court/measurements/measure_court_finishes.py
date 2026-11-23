"""Sample No. 3 brick and render at their registered depths; compare the authored PNG's mortar phase."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates
from scipy.signal import find_peaks

from register_court import Camera
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'source'))
from court_finishes import BRICK, CAST, REPEAT_METRES, FILENAMES, NORMAL_FILENAMES, lattice, PHASE_X, PHASE_V, BED_DRIFT

BRICK_READINGS = {'left of opening': (-2.51,5.93,-2.06,6.20),
                  'near pier, lower': (-.30,4.77,.045,5.24),
                  'near pier, upper': (-.295,5.88,.04,6.065)}
RENDER_READINGS = {'upper shaft':(.02,1.75,.15,2.05), 'middle shaft':(-.05,1.21,.09,1.56),
                   'lower shaft':(-.11,.96,-.012,1.13)}


def sample(camera, photo, bounds, depth, density):
    x0,z0,x1,z1=bounds
    x,z=np.meshgrid(np.arange(x0,x1,1/density),np.arange(z1,z0,-1/density))
    xyz=np.stack([x,x*0+depth,z])
    ray=camera.k@camera.r@(xyz.reshape(3,-1)-camera.c[:,None])
    pixels=(ray[:2]/ray[2]).reshape(2,*x.shape)
    rgb=np.stack([map_coordinates(photo[:,:,k], pixels[[1,0]],order=1) for k in range(3)],axis=-1)
    return x,z,pixels,rgb


def percentiles(rgb):
    return np.percentile(rgb.reshape(-1,3),[10,50,90],axis=0).round(1).tolist()


def brick_test(x,z,rgb,texture):
    width,height=REPEAT_METRES[BRICK]
    lum=rgb.mean(axis=-1)
    observed=np.clip(lum-gaussian_filter(lum,7),-10,20)
    def rendered(du,dv,drift):
        u,v=(x+du)/width,(z+dv+x*drift)/height
        coords=[v*texture.shape[0]-.5,u*texture.shape[1]-.5]
        predicted=map_coordinates(texture,coords,mode='grid-wrap',order=1)
        predicted-=gaussian_filter(predicted,7)
        split=x.shape[1]*2//3
        return {label:dict(pixels=observed[:, col].size,
                           pearson_r=float(np.corrcoef(observed[:,col].ravel(),predicted[:,col].ravel())[0,1]))
                for label,col in [('fit_left_columns',slice(None,split)),('held_out_right_columns',slice(split,None))]}
    ac={}
    for axis,title in [(0,'across_courses'),(1,'along_courses')]:
        profile=observed.mean(axis=1-axis)
        profile-=gaussian_filter1d(profile,18)
        corr=np.correlate(profile,profile,'full')[len(profile)-1:]
        peaks=find_peaks(corr/corr[0],height=.15)[0]
        ac[title]=[dict(samples=int(i),study_m=float(i/520)) for i in peaks[:8]]
    edge,_=lattice(x+PHASE_X,-(z+PHASE_V+x*BED_DRIFT))
    return dict(filtered_profile_autocorrelation_peaks=ac, unphased_colour=rendered(0,0,0),
                calibrated_colour=rendered(PHASE_X,PHASE_V,BED_DRIFT),
                clay_interior_srgb_percentiles=percentiles(rgb[edge>.010]),
                joint_centres_srgb_percentiles=percentiles(rgb[edge<.0030]))


def measure(photo_file):
    original=photo_file.read_bytes()
    if hashlib.sha256(original).hexdigest()!='784954307853a7cef1f1d783366b63ab3bc58af191d99c574ee20a29645da44e':
        raise ValueError('Expected the native Livelikerw photograph, 4912 by 3264')
    camera=Camera()
    frame=np.asarray(Image.open(photo_file).convert('RGB'))
    source=HERE.parent/'source'
    tex=np.asarray(Image.open(source/FILENAMES[BRICK])).mean(axis=-1)
    brick,render={},{}
    for title,areas,density,depth,out in [(BRICK,BRICK_READINGS,520,1.359,brick),(CAST,RENDER_READINGS,400,0.,render)]:
        for tag,bounds in areas.items():
            x,z,pixels,rgb=sample(camera,frame,bounds,depth,density)
            uv=pixels.reshape(2,-1)
            record=dict(metre_bounds_x0_z0_x1_z1=bounds,depth_m=depth,sampling_per_m=density,
                        pixel_count=x.size,native_photo_box_xy=[uv.min(1).tolist(),uv.max(1).tolist()],
                        actual_srgb_percentiles_10_50_90=percentiles(rgb))
            if title==BRICK:
                record.update(brick_test(x,z,rgb,tex))
            else:
                a=rgb.astype(float)
                record['six_sample_highpass_sigma_srgb']=np.std(a-gaussian_filter(a,sigma=(6,6,0)),axis=(0,1)).round(3).tolist()
            out[tag]=record
    digest=lambda f: hashlib.sha256((source/f).read_bytes()).hexdigest()
    return dict(photo='https://commons.wikimedia.org/wiki/File:Dafu_Li_Shanghai.JPG',photo_sha256=hashlib.sha256(original).hexdigest(),
                photographer='Livelikerw',date='2016-02-06',reference_licence='CC BY-SA 4.0',
                plane='The red wall is measured at Y=1.359 m. The render is read at the plaque-bearing shaft, Y=0. Camera parameters and the conditional metric scale are in court-camera.json; true absolute building dimensions remain uncertain.',
                colour_method='Bilinear RGB from the original JPEG. The lighting differs across the two piers. Brick pigments are chosen between the east and west readings; a lighter, less saturated mortar is visible. The render is in deep shade and no neutral reference permits unique recovery of absolute albedo.',
                brick=brick, render=render,
                brick_interpretation=dict(stretcher_m=.308*2/3,header_m=.308/3,course_m=.05403,group_m=.308,repeat_m=REPEAT_METRES[BRICK],
                    standalone_left_pair_and_two_courses_m=[.308,.111],standalone_lower_right_pair_and_two_courses_m=[.300,.107],
                    smallest_upper_right_patch='The total width is close to one long-short pair. Its course pitch is usable, but the horizontal brick length is weakly constrained.',
                    apparent_row_phase_drift_m_per_m=BED_DRIFT,glb_phase_u_v_m=[PHASE_X,PHASE_V],
                    fit='Compare a blurred grout-centre field against a local high-pass of the source on the left two thirds. Search 0.300, 0.304, 0.308 m groups; two-course pitches 0.105 to 0.113 m at 0.00018 increments, shear -0.032 to +0.034 at 0.003 increments and within-tile translation on a 64 by 64 lattice. Report actual PNG correlations for the untouched right third. Apparent slope in the registered wall can include camera calibration error. Different piers do not share one perfectly straight mortar phase.'),
                render_interpretation='A fine, weathered, grey-pink cast surface is legible. No natural repeat length or uniquely measurable grain depth was identified. The 0.42 by 0.52 m tile, fine relief and trowel streaks are procedural rendering choices.',
                original_assets={n:dict(colour=FILENAMES[n],colour_sha256=digest(FILENAMES[n]),
                                        tangent_normal=NORMAL_FILENAMES[n],normal_sha256=digest(NORMAL_FILENAMES[n]),
                                        repeat_u_v_metres=REPEAT_METRES[n]) for n in FILENAMES},
                authored_licence='MIT; the generator uses no source-photo pixels')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_photo',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    print('Measuring the registered wall and gatepost',flush=True)
    args.output.write_text(json.dumps(measure(args.original_photo),indent=2,ensure_ascii=False)+'\n')
