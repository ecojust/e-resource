"""Survey the shallow brick fan and stone sill on the 2012 courtyard window photograph."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

from PIL import Image

LEFT_LIMIT, RIGHT_LIMIT = 77.5, 428.0
CENTER_X = 251.5

def ref_y(x):
    return 69.0 + .00157*(x-CENTER_X)**2

def bright_joints(photo):
    # Half-resolution native JPEG decoding still gives 3.18 samples per working pixel.
    image = Image.open(photo)
    assert image.size == (3240, 4320)
    image.draft('RGB', (1620, 2160))
    factor = image.width / 510
    region = image.crop((0, 0, image.width, round(158*factor))).convert('RGB')
    def green(x, y):
        return region.getpixel((round(x*factor), round(y*factor)))[1]
    profile = []
    for i in range(4*76, 4*432):
        x = i*.25
        value = median(green(x, ref_y(x)+j*.4) for j in range(-4, 5))
        profile.append((x, value))
    peaks=[]
    for i,(x,val) in enumerate(profile):
        if i<15 or i+15>=len(profile):
            continue
        values = [v for _,v in profile[i-15:i+16]]
        contrast = val-median(values)
        if val==max(values) and contrast>=50 and (not peaks or x-peaks[-1][0]>3):
            if x<231 or 274<x:
                peaks.append([x, contrast])
    def candidate(vanishing_y):
        offsets=[]
        for x,contrast in peaks:
            y=ref_y(x)
            if y>100 or x<91 or x>413:
                continue
            for dy in (-7,-5,5,7):
                xx=x+(CENTER_X-x)*dy/(vanishing_y-y)
                if 105<y+dy<143:
                    continue
                bright=green(xx,y+dy)
                offsets.append(bright-(green(xx-2,y+dy)+green(xx+2,y+dy))*.5)
        return sum(offsets)/len(offsets)
    fits=[(candidate(y),y) for y in range(280,631,5)]
    return peaks,max(fits)[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('photo',type=Path)
    p.add_argument('out',type=Path)
    args=p.parse_args()
    digest = hashlib.sha256(args.photo.read_bytes()).hexdigest()
    assert digest=='fa8e936ac5c3bbc1d7ea7f4e3af857c2fd00f43c2bd33bf54a3f56ba7b5eb393'
    joints,convergence_y=bright_joints(args.photo)
    # The extreme left first joint is crossed by a cable on the normal sampling arc.
    # Its oblique upper segment can still be traced at the higher, unobstructed part.
    left=[LEFT_LIMIT,84.75,*[x for x,c in joints if 88<x<231],233.25]
    right=[271.0,*[x for x,c in joints if 274<x<427],RIGHT_LIMIT]
    document=dict(
        photo_sha256=digest, original_size=[3240,4320], working_size=[510,680],
        source='2012 courtyard window, pixel x right and y down. The separate gable photograph was not used.',
        strip=dict(y='69+0.00157*(x-251.5)^2',step_x=.25,halfband_y=1.6,green_peaks=joints),
        radial_lines_x_at_strip=[left,right], radial_guide_point=[CENTER_X,convergence_y],
        outer_curve=[[77.5,103.6],[94,95.8],[109,88.9],[128,80.5],[150,73.2],[179,65.2],[205,60.5],[229.5,56.5],[273,55.5],[295,59.9],[322,64.0],[349,69.7],[373,76.0],[395,85.4],[410,93.1],[428,101.5]],
        first_bed=[[83,126.8],[102,120.4],[130,111.0],[154,102.4],[182,94.0],[205,88.8],[231,85.3],[272,83.7],[296,86.1],[320,90.3],[344,96.3],[366,103.2],[393,112.7],[417,122.3],[433,128.1]],
        intrados=[[120,118.5],[133,134.0],[150,155.5],[158,155.0],[179,147.8],[198,141.0],[222,138.3],[250,137.5],[276,137.1],[299,136.1],[313,142.1],[334,149.9],[351,154.5],[358,154.0],[369,138.0],[385,118.3]],
        key_upper_joints=[[231.9,53],[240.6,53],[248.5,53],[256.1,53],[263.2,53],[273.0,53]],
        key_lower_joints=[[241.7,138.5],[247.0,138],[251.9,137.7],[257.6,137.5],[262.3,137.2],[268.1,137.1]],
        key_bed_levels=[[99.3],[77.6],[98.4],[77.9],[98.1]],
        sill=dict(upper_rear=[[119.0,576.5],[407.5,568.9]],upper_nose=[[111.5,582.4],[416.2,575.0]],
                  lower_nose=[[112.3,601.0],[415.0,595.4]],lower_bevel=[[116.7,604.6],[410.6,599.4]]),
        apron_left=[[122.4,604.5],[127.1,612.4],[136.9,626.5],[130.6,641.3],[129.4,656.3],[133.0,679.5]],
        apron_right=[[404.7,599.7],[399.4,610.0],[391.7,625.2],[400.0,639.7],[401.2,653.3],[397.1,679.5]],
        apron_beds=[[603,599],[616,612.8],[627.7,624.5],[641.6,637.8],[655.3,651.1],[669.3,665.4],[679.5,679.5]],
        apron_head_joints=[[150,178,240,271,331,360],[167,226,285,344],[182,211,241,303,376],[153,195,242,318,359],[178,211,266,319,373],[151,197,236,283,345]],
        uncertainty='Mortar centers usually resolve to about 1 working pixel. Service wires mask portions at y108–145. Course contours through them interpolate only between visible runs. Secondary brick depth, setbacks and stone depth are nominal. The skirt ends at the photograph crop. Surface losses are not surveyed openings.')
    args.out.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': main()
