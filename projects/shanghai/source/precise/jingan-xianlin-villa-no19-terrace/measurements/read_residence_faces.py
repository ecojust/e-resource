"""Rectify the three visible walls of No.19 in Fayhoo's 2015 photograph."""
from pathlib import Path
import argparse
import json
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'source'))
from courtyard_photo_plane import P, fixed_plane, pixel

def rectified(photo, axis, fixed, limits, pixels_per_metre=90):
    lo, hi, bottom, top = limits
    v,u = np.mgrid[:round((top-bottom)*pixels_per_metre), :round((hi-lo)*pixels_per_metre)]
    span=lo+u/pixels_per_metre
    z=top-v/pixels_per_metre
    constant=np.full_like(span,fixed)
    x,y=(span,constant) if axis==1 else (constant,span)
    homogeneous=P@np.stack((x,y,z,np.ones_like(x))).reshape(4,-1)
    ix,iy=np.rint(homogeneous[:2]/homogeneous[2]).astype(int)
    source=np.asarray(photo.convert('RGB'))
    valid=(ix>=0)&(iy>=0)&(ix<source.shape[1])&(iy<source.shape[0])
    result=np.zeros((ix.size,3),np.uint8)
    result[valid]=source[iy[valid],ix[valid]]
    return Image.fromarray(result.reshape(u.shape+(3,)))

# The cropped façade rectifications are working aids. The recorded points are
# in the unmodified 2144 × 1424 original, and use both sides of the corner.
OBSERVATIONS={
 'end_wall_under_terrace':(0,1.913,{'brick_corner_head':[1079,479],'stepped_course_bottom':[1078,824],
    'south_sash_left_jamb':[1134,524],'middle_panel_sill':[1220,764],'bay_lower_moulding':[1080,930]}),
 'upper_wall':(0,0,{'eaves_at_corner':[926,140],'dark_open_leaf_left':[952,269],
    'dark_open_leaf_right':[1035,257],'glazed_extension_stile':[1180,219]}),
 'long_wall':(1,0,{'eaves_near_corner':[925,150],'eaves_far_slope_turn':[452,390],
    'far_eaves_end':[332,508],'near_drain_at_foot':[883,1268],'central_downpipe':[626,740],
    'central_cage_left':[527,667],'central_cage_right':[593,650],
    'yellow_quoin_edge':[1078,837],'astragal_at_wall_end':[902,874]}),
}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    image=Image.open(args.photo)
    if image.size!=(2144,1424):
        raise ValueError('Use the 2144 × 1424 original')
    for name,axis,fixed,limits in [('side',1,0,(-13,.11,0,11.35)),('bay',0,1.913,(-.12,5.40,0,7.15)),('upper',0,0,(-.15,6.0,7.01,11.2))]:
        rectified(image,axis,fixed,limits).save(args.output/(name+'.jpg'),quality=93)
    rows={}
    for name,(axis,value,marks) in OBSERVATIONS.items():
        points={}
        for label,uv in marks.items():
            # The exposed yellow corner is on X=1.913, outside the main Y=0 wall.
            xyz=fixed_plane(*uv,axis,value)
            points[label]={'original_px':uv,'on_named_plane_m':xyz}
        rows[name]=dict(axis='XYZ'[axis],face_m=value,points=points)
    record=dict(source='https://commons.wikimedia.org/wiki/File:Xianlin_Bieshu.JPG',
                source_size_px=[2144,1424],registration='courtyard-camera.json',planes=rows,
                limits='Scale follows 30 brick courses, approximately ±9.4%. The clipped crown, tree-obscured run of the roof and back wall are estimated.')
    (args.output/'no19-facade-measurements.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
