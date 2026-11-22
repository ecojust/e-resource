"""Detect independent runs of bright blade crests on the native November 2016 photograph."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import find_peaks

REFERENCE='72a75771cbbbfb77d2f129bde0b295394a61231c3b9e0552ae129d4e56f7f12b'
# Native pixel columns and ranges. These vertical lanes lie entirely inside the second shutter leaf of the middle bay.
LANES=[(1991,2006),(2010,2026),(2030,2046)]
BANDS={'upper':(917,1230),'lower':(1267,2114)}
def measure(path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=REFERENCE:raise ValueError('Photo checksum mismatch')
    image=np.asarray(Image.open(path).convert('L'))
    if image.shape!=(2392,4082):raise ValueError('Expected native 4082 × 2392 photograph')
    runs=[]
    for L,R in LANES:
        for name,(top,bottom) in BANDS.items():
            brightness=image[top:bottom,L:R].mean(axis=1)
            peaks,_=find_peaks(brightness,distance=18,prominence=5)
            rows=peaks+top
            runs.append(dict(leaf='middle window, second from left',band=name,x_range=[L,R],y_range=[top,bottom],native_bright_centres=rows.tolist(),count=len(rows),median_pitch_px=float(np.median(np.diff(rows)))))
    return dict(source='言衣草《上海 延安中路 卢永祥公馆》，2016-11-21发布，图像EXIF 2016-11-02 16:41:43',article='https://blog.sina.cn/dpool/blog/s/blog_a598306e0102xev6.html',original_url='https://s14.sinaimg.cn/large/003216vszy76zbuRUN75d',source_sha256=REFERENCE,runs=runs,scope='中窗实测叶片；轮廓和叶架在另两窗可辨。右窗下段受棕榈遮挡，重复构造按中窗。')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('image',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();b=measure(a.image);a.output.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
    print([(r['band'],r['count'],r['median_pitch_px'])for r in b['runs']])
