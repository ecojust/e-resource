"""Measure the historical roof inscription from two published images of the Tanggu Road apartment crown."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon

IMAGE_CORNERS = {
    # Intersections of the four long perimeter rims, before clipping their corners.
    '2017_close': [[225.,80.55],[354.3,69.2],[354.1,92.8],[224.7,103.9]],
    '2015_press': [[354.4,85.8],[417.2,82.5],[417.0,93.8],[354.3,97.4]],
}
GRID = np.float32([[0,0],[647,0],[647,119],[0,119]])
LETTERS = '1912—1936'
BANDS = [(52,99),(101,154),(154,203),(205,261),(265,378),
         (392,442),(444,495),(495,546),(549,598)]


def normalized(points):
    return [[round(x/647-.5,6),round(.5-y/119,6)] for x,y in points]


def rectified(file, corners):
    mat=cv2.getPerspectiveTransform(np.float32(corners),GRID)
    image=np.asarray(Image.open(file).convert('RGB'))
    return cv2.warpPerspective(image,mat,(648,120),flags=cv2.INTER_CUBIC),mat


def longest_outline(mask):
    contours,_=cv2.findContours(mask.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    return max(contours,key=cv2.contourArea)


def trace(close,press):
    near,hn=rectified(close,IMAGE_CORNERS['2017_close'])
    far,hf=rectified(press,IMAGE_CORNERS['2015_press'])
    rgb=near.astype('float32')
    pale=(rgb.mean(2)>118)&(rgb[:,:,1]>.90*rgb[:,:,0])&(rgb[:,:,2]>.82*rgb[:,:,0])
    outline=longest_outline(pale)
    face=Polygon(cv2.approxPolyDP(outline,2.35,True).reshape(-1,2))
    # The upper exposure shows the dark perimeter for around 1.4–2 source pixels.
    # Broadening the pale contour by 7.4 grid units equals 1.48 original pixels.
    outer=face.buffer(7.4,quad_segs=3,join_style='round').simplify(1.7)
    close_luma=cv2.cvtColor(near,cv2.COLOR_RGB2GRAY)
    press_luma=cv2.cvtColor(far,cv2.COLOR_RGB2GRAY)
    glyphs=[]; checks=[]
    for i,((x0,x1),char) in enumerate(zip(BANDS,LETTERS),1):
        roi=close_luma[17:103,x0:x1]
        contours,tree=cv2.findContours((roi<110).astype('uint8'),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        index=max(range(len(contours)),key=lambda n:cv2.contourArea(contours[n]))
        def ring(k):
            pts=cv2.approxPolyDP(contours[k],.98,True).reshape(-1,2)+[x0,17]
            return normalized(pts)
        holes=[ring(k)for k in range(len(contours))if tree[0,k,3]==index and cv2.contourArea(contours[k])>=20]
        near_shape=Polygon(ring(index),holes)
        assert near_shape.is_valid and (len(holes)==(1 if char in '96' else 0)), (char,holes)
        mask=np.zeros((120,648),'uint8')
        cv2.drawContours(mask,[contours[index]+np.array([x0,17],dtype='int32')],-1,1,-1)
        for k in range(len(contours)):
            if tree[0,k,3]==index:
                cv2.drawContours(mask,[contours[k]+np.array([x0,17],dtype='int32')],-1,0,-1)
        core=cv2.erode(mask,np.ones((3,3),'uint8')).astype(bool)
        surroundings=cv2.dilate(mask,np.ones((17,17),'uint8')).astype(bool)&~cv2.dilate(mask,np.ones((7,7),'uint8')).astype(bool)
        inside,outside=map(float,(np.median(press_luma[core]),np.median(press_luma[surroundings])))
        checks.append(dict(position=i,character=char,independent_stroke_median=inside,independent_surround_median=outside,
                           darkening_native_luma=round(outside-inside,2)))
        glyphs.append(dict(position=i,character=char,outline=ring(index),counters=holes))
    def signature(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(frame='X increases right, Z increases up. Both axes are normalized to the full rim width and height separately.',
                reading=LETTERS,image_size_close=list(Image.open(close).size),image_size_press=list(Image.open(press).size),
                published_sources={
                  '2015_press':dict(publication='人民网, 王文娟, 2015-10-29',article_reprint='https://sdqy.dzwww.com/jdtp/201510/t20151030_13263603.htm',
                    photo='https://sh.people.com.cn/NMediaFile/2015/1029/LOCAL201510291737000146830179068.JPG',sha256=signature(press)),
                  '2017_close':dict(publication='沂蒙生活，2017-07-26，每日头条转载组图',page='https://kknews.cc/zh-sg/history/6pzgb9q.html',
                    photo='https://i2.kknews.cc/3AgP4116TsFVW5T2jZhvvNwmasG5Ym5ZQVpw2X8/0.jpg',sha256=signature(close),
                    date_note='A wider image in the same series bears 2016/05/30. The local close-up retains only part of the timestamp.')},
                image_corners=IMAGE_CORNERS,image_to_rectified={'2017_close':hn.tolist(),'2015_press':hf.tolist()},
                stored_grid=[648,120],apparent_height_to_width=.181,
                ratio_scope='Source image proportions. The published exposures give about 0.18. The physical width, height and placement can be supplied independently.',
                source_edge_error_px={'2017_close':1.0,'2015_press':1.5},
                face=normalized(face.exterior.coords[:-1]),backing=normalized(outer.exterior.coords[:-1]),
                glyphs=glyphs,independent_press_contrast=checks,
                interpretation='The plaque reads 1912—1936. The available images establish the lettering and rim. The dates’ historical meaning and the exact relief depth are unconfirmed.')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('close',type=Path);ap.add_argument('press',type=Path);ap.add_argument('result',type=Path)
    args=ap.parse_args();data=trace(args.close,args.press);args.result.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print([row['darkening_native_luma'] for row in data['independent_press_contrast']])
