"""Compare the photographed seven-bay foot line against the 2024 image at the low porch."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/xuhui-yueyang-320-research-building/footprint-review.json'


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--tiles',required=True,type=Path,help='Directory containing the named raw JPEGs from the footprint review')
    cli.add_argument('--out',type=Path,default=HERE/'portico-shadow-comparison.json')
    args=cli.parse_args()
    src=json.loads(SOURCE.read_bytes())
    entries=[r for r in src['image_layers']['receipts']if r['date']=='2024-01-18']
    ox=min(r['x']for r in entries)*256;oy=min(r['y']for r in entries)*256
    image=Image.new('RGB',((max(r['x']for r in entries)+1)*256-ox,(max(r['y']for r in entries)+1)*256-oy))
    for r in entries:
        path=args.tiles/r['filename'];assert sha256(path.read_bytes()).hexdigest()==r['sha256']
        with Image.open(path) as im:
            im.load();image.paste(im,(r['x']*256-ox,r['y']*256-oy))
    frame=src['author_frame'];lon=frame['anchor']['lng'];lat=frame['anchor']['lat'];bearing=math.radians(frame['runtime_heading_deg'])
    a=np.array([[math.cos(bearing),math.sin(bearing)],[-math.sin(bearing),math.cos(bearing)]])
    count=2**19*256
    origin=np.array([(lon+180)*count/360,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)*count/2])-[ox,oy]
    ground_per_px=2*math.pi*6371008.8*math.cos(math.radians(lat))/count
    def pixel(i,j):
        e,n=a@[(i-245)/4.4,(222-j)/4.4]
        return origin+np.array([e,-n])/ground_per_px
    c=pixel(0,0);x=pixel(1,0)-c;y=pixel(0,1)-c
    im=image.transform((490,280),Image.Transform.AFFINE,(x[0],y[0],c[0],x[1],y[1],c[1]),Image.Resampling.BICUBIC)
    # A single fixed row band crosses the dark traces directly below the roof rim.
    intensity=np.asarray(im.convert('L'))[248:252,202:298].mean(0)
    smooth=gaussian_filter1d(intensity,.9)
    ix=find_peaks(-smooth,distance=7,prominence=9)[0]
    dark=(ix+202-245)/4.4
    expected=.716+(np.arange(8)-3.5)*17.69/7
    # Seven clear minima survive native-pixel sampling. The far southern edge is
    # mingled with canopy shadow; there is no independent eighth aerial witness.
    assert len(dark)==7
    relative=dark-dark[0]
    expected_offsets=np.arange(len(dark))*17.69/7
    offset=np.median(relative-expected_offsets)
    residual=relative-expected_offsets-offset
    spacing=(dark[-1]-dark[0])/(len(dark)-1)
    assert 2.25<spacing<2.8 and max(abs(residual))<1.15
    report=dict(source_review_sha256=sha256(SOURCE.read_bytes()).hexdigest(),checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                layer_date='2024-01-18',inputs=[dict(filename=r['filename'],sha256=r['sha256'])for r in entries],
                rectified_scale_px_per_m=4.4,trace_sample_foreground_y_m=[(222-248)/4.4,(222-251)/4.4],
                sample_luminance=intensity.tolist(),dark_lobes_x_m=dark.tolist(),modeled_support_x_m=expected.tolist(),
                average_lobe_spacing_m=spacing,modeled_arch_bay_m=17.69/7,number_of_visible_minima=len(dark),consecutive_intervals=len(dark)-1,relative_offset_fit_m=offset,
                max_residual_after_one_translation_m=float(max(abs(residual))),
                interpretation_zh='门廊檐缘前方同一固定横样带的原始瓦片可从七段局部暗带取得六个连续间距，与拟建七券八支点的节距相符。靠南的边部与树冠阴影混合，不能逐支点从航片定数。记录一次整体平移后的相对间隔，阴影不等于柱脚坐标。七券数量由归档斜照与2014年地面原照独立确认。')
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(spacing,offset,max(abs(residual)))


if __name__=='__main__':
    main()
