"""Read the ten stair nosings, roof tile courses and porch edges from Fayhoo's original JPEG."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

HASH='8551e1a2fe029e051ceae4b45796ca4e6133112b45efb282d19c6ab78e15b0f4'
SOURCE='https://commons.wikimedia.org/wiki/File:Zhuzhai_(Changlelu_325_Hao).JPG'
NAMES=['lower bowl front and stem','upper left ball','forward-return arch, left spring','arch, right spring']
def measure(path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=HASH:
        raise ValueError('Use the full 2037 × 1358 image of 4 April 2015.')
    with Image.open(path) as image:
        rgb=np.asarray(image.convert('RGB'),dtype=float)
    grey=rgb@np.array([.299,.587,.114])
    stations=[]
    for x in [500,545,580,625,700,751,770]:
        sample=grey[904:1090,x:x+9].mean(axis=1)
        grad=-np.gradient(sample)
        points,_=find_peaks(grad,distance=14,prominence=10)
        obs=[int(q+904) for q in points]
        if len(obs)!=10:raise ValueError((x,obs))
        stations.append({'column':x+4,'dark_edge_row':list(reversed(obs))})
    lines=[]
    for i in range(10):
        x=np.array([a['column'] for a in stations]);y=np.array([a['dark_edge_row'][i] for a in stations])
        slope,centre=np.polyfit(x-625,y,1)
        lines.append({'index_from_bottom':i+1,'u_ref':625,'v_at_ref':round(centre,4),'dv_du':round(slope,6),
                      'largest_residual_px':round(float(max(abs(y-slope*(x-625)-centre))),3)})
    tile_rows=[]
    for y,left,right in [(520,488,778),(570,454,848),(595,438,850)]:
        a=gaussian_filter1d(grey[y-1:y+2].mean(axis=0),1.35)
        peaks,_=find_peaks(a[left:right+1],distance=20,prominence=10)
        centres=(peaks+left).tolist()
        tile_rows.append({'v':y,'visible_range':[left,right],'convex_highlights_u':centres})
    return {'source':SOURCE,'author':'Fayhoo','license':'CC BY-SA 3.0','sha256':HASH,
            'size':[2037,1358],'exif':{'model':'Nikon D90','focal_mm':40,'equivalent_35mm':60,'capture':'2015-04-04 13:38:16'},
            'stairs':{'column_readings':stations,'nosings':lines,
                      'definition':'Gradient points mark the dark lower arris beneath each stone tread. The ten aligned edges were measured in seven separate image columns.',
                      'lower_post_axes_on_ground_px':[[374,1096],[842,1094]],
                      'upper_post_axes_at_landing_px':[[469,908],[887,907]],
                      'upper_right_limit':'The foreground curved wing covers part of the upper right finial. Its visible edge and cap only bound the axis.'},
            'tiles':tile_rows,
            'front_arch_intrados_px':[[519,904],[519,844],[519,785],[522,754],[535,719],[552,693],[580,669],[615,649],[650,637],[682,633],[714,634],[748,642],[784,660],[813,684],[837,716],[850,747],[854,778],[854,822]],
            'front_arch_faces':{'left_jamb_outer_x':458,'sill_y':906,'eaves_front_lower':[[433,628],[866,627]],
                                'eaves_noses':[[434,611],[866,610]],'rear_roof_edge':[[536,445],[769,443]],
                                'left_roof_rake':[[434,609],[540,446]]},
            'stonework':{'lower_dishes':[[379,856],[842,854]],'upper_balls':[[468,775],[887,775]],
                         'left_dish_width_px':76,'left_ball_diameter_px':35,
                         'description':'Two shallow dishes on the lower newels, a ball on each upper cap, gently curved cheeks, and a sloping coping over short uprights.'},
            'doors':{'meeting_joint':[[742,683],[742,904]],'handles_centre':[[729,795],[755,794]],
                     'bottom_patches':[[705,903],[744,903]],'notes':'Dark glazed leaves and paired vertical pulls carry a horizontal latch. The photograph resolves the recess and threshold.'}}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('photo',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();report=measure(args.photo)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(len(report['stairs']['nosings']),[(r['v'],len(r['convex_highlights_u']))for r in report['tiles']])
