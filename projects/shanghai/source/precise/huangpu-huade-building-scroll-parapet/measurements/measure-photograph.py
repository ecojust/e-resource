"""Measure the two parapet apertures and eighteen soffit bosses in the upright 2015 image."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

SOURCE_SHA='63c2cfb2323c5a30f64ce5fb040875faaf1e44c5150e9651e992a54033aba3e2'
SOURCE_CROP=(253,2350,1271,2946)
# Inspection boxes locate each dark stone-edge reflection; no model geometry is used.
FIELD_MARKS=[
 [(312,321),(277,333),(340,334),(243,347),(305,348),(366,347),(272,360),(332,360),(300,372)],
 [(574,449),(539,458),(597,458),(507,469),(565,470),(620,470),(531,481),(586,481),(554,492)],
]


def clipped_crop(path):
    with Image.open(path) as im:
        if im.getexif().get(274)!=6 or im.size!=(5312,2988):
            raise ValueError('Expected original SM-G9009W photograph with EXIF orientation 6')
        a,b,c,d=SOURCE_CROP
        # Inverse of a clockwise rotation, crop before transposing to save memory.
        box=(b,im.height-c,d,im.height-a)
        return np.asarray(im.crop(box).transpose(Image.Transpose.ROTATE_270).convert('L'),dtype=float)


def crossing(a,b,t):
    return (t-a)/(b-a)


def aperture_boundaries(image,box,columns):
    x0,y0,x1,y1=box
    out=[]
    for x in columns:
        values=image[y0:y1+1,x]
        background=np.median(np.r_[values[:3],values[-3:]])
        shade_value=np.percentile(values,4)
        threshold=(background+shade_value)/2
        dark=np.flatnonzero(values<threshold)
        if len(dark)<2 or dark[0]==0 or dark[-1]>=len(values)-1:
            continue
        a,b=dark[0],dark[-1]
        top=y0+a-1+crossing(values[a-1],values[a],threshold)
        bottom=y0+b+crossing(values[b],values[b+1],threshold)
        out.append(dict(x=x,upper_y=round(top,3),lower_y=round(bottom,3),
                        threshold=round(threshold,2),contrast=round(background-shade_value,2)))
    return out


def boss_crowns(image):
    output=[]
    for marks in FIELD_MARKS:
        rows=[]
        for seed_x,seed_y in marks:
            # Inspect the centre of the dark cap above each circular underside.
            left,right=seed_x-11,seed_x+12
            top,bottom=seed_y-6,seed_y+7
            roi=image[top:bottom,left:right]
            bg=np.percentile(roi,86)
            weights=np.clip(bg-roi,0,None)**2
            cols=np.arange(left,right);lines=np.arange(top,bottom)
            mass=weights.sum()
            if mass<=0:
                raise ValueError('Empty shadow band')
            center=[float(np.dot(weights.sum(0),cols)/mass),float(np.dot(weights.sum(1),lines)/mass)]
            rows.append(dict(search=[left,top,right,bottom],shadow_crown=[round(q,3)for q in center]))
        output.append(rows)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--holdout',action='store_true',help='Use separate large-arch columns and both small lower openings')
    args=parser.parse_args()
    digest=hashlib.sha256(args.photo.read_bytes()).hexdigest()
    if digest!=SOURCE_SHA:
        raise ValueError('Unexpected original photographic file')
    pixels=clipped_crop(args.photo)
    holes=[aperture_boundaries(pixels,(477,264,514,301),[484,487,490,493,496,499,502,505,508]),
           aperture_boundaries(pixels,(707,387,746,421),[719,722,725,728,731,734,737,740])]
    if args.holdout:
        holes=[aperture_boundaries(pixels,box,columns) for box,columns in [
            ((477,264,514,302),[483,485,488,491,494,497,500,503,506,507,509]),
            ((707,387,746,421),[718,720,723,726,729,732,735,738,739]),
            ((484,309,511,335),[494,496,498,500,502,504]),
            ((722,429,743,449),[728,730,732,734,736])]]
    data=dict(photo_sha256=digest,photo='Antigng, Wikimedia Commons, 2015-07-20, CC BY-SA 4.0',
              source_url='https://commons.wikimedia.org/wiki/File:%E5%8D%8E%E5%BE%B7%E5%A4%A7%E6%A5%BC.jpg',
              crop_upright_xyxy=list(SOURCE_CROP),pixel_space='pixel centres of the 1018 × 596 unscaled crop',
              method='Vertical half-contrast crossings at preselected x columns; upper and lower edge are measured independently. Boss landmarks mark the visible dark crown shadow, not the geometrical centre of a disk.',
              apertures=holes,soffit_boss_crowns=boss_crowns(pixels))
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('grid',pixels.shape,'hole columns',[len(q) for q in holes],'bosses',[len(q) for q in data['soffit_boss_crowns']])


if __name__=='__main__':
    main()
