"""Compare seven lit letter faces to the plaque in the reference and ordinary WebGL view."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

BOXES=[(106,128),(129,150),(151,176),(176,201),(202,229),(230,252),(253,277)]
CHARS="上海民政博物馆"
WEIGHTS=np.array([.2126,.7152,.0722])


def calculate(reference,old,pilot,revised):
    pictures={}
    for key,path in [("first_public",old),("intermediate",pilot),("revised",revised)]:
        with Image.open(path) as im:
            if im.size!=(644,448):raise ValueError("Expected the ordinary 920×640 desktop view at device pixel ratio 0.7")
            pictures[key]=np.asarray(im.convert('RGB'),dtype=float)
    target=pictures["revised"]
    rows=[]
    for char,(x0,x1) in zip(CHARS,BOXES):
        tile=target[161:188,x0:x1]
        # The seven editable shapes keep their position through all three materials.
        # Fix the pixel mask once, on the final neutral-metal faces, to compare the same strokes.
        faces=(tile[:,:,0]-tile[:,:,1]<4.2)&(tile[:,:,1]>88.)
        if faces.sum()<20:raise ValueError("Insufficient unblended stroke area")
        s={"character":char,"screen_box_ltrb":[x0,161,x1,188],"measured_pixels":int(faces.sum())}
        for key,im in pictures.items():s[key]=np.median(im[161:188,x0:x1][faces],axis=0).round(1).tolist()
        rows.append(s)
    board={}
    for key,im in pictures.items():
        b=np.concatenate([im[156:161,101:278].reshape(-1,3),im[189:193,104:285].reshape(-1,3)])
        board[key]=np.median(b,axis=0).round(1).tolist()
    measured=json.loads(reference.read_bytes())
    for r,t in zip(rows,measured['characters']):
        if r['character']!=t['character']:raise ValueError("Incorrect reference order")
        r['archive_2014']=t['median_lit_srgb']
    board['archive_2014']=measured['plaque_lit_median_srgb']
    ratios={}
    for key in board:
        metal=np.median([r[key] for r in rows],axis=0)
        ratios[key]=round(float((metal@WEIGHTS)/(np.array(board[key])@WEIGHTS)),3)
    instant=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(archive_source_original_sha256=measured['source_sha256'],
                ordinary_page="puyutang-museum-south-front.html",ordinary_view="front",
                ordinary_viewport_css_px=[920,640],device_pixel_ratio=.7,
                crop_method="Coordinates in the original browser PNG. Least-red lit faces selected in the revised image and sampled unchanged in all three exposures. Neutral edge antialiasing is included. Original archive exposure uses its independent seven glyph masks and brown board coordinates in museum-sign-layout.json.",
                screenshots_sha256={key:instant(path) for key,path in [('first_public',old),('intermediate',pilot),('revised',revised)]},
                plaque_median_srgb=board,seven_letter_face_srgb=rows,
                relative_lit_face_to_plaque_weighted_srgb=ratios,
                qualifications="The 2014 archive and the real-time viewer use different illumination. These are appearance checks under each exposure; they are not measurements of the material's spectral reflectance.")

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['reference','old','pilot','revised','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();r=calculate(a.reference,a.old,a.pilot,a.revised)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['plaque_median_srgb'],r['relative_lit_face_to_plaque_weighted_srgb'])
