"""Trace the visible Ionic capital of the former Chung Foo Union Bank from Fayhoo's street photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter,gaussian_filter1d,map_coordinates

SOURCE_SHA = "c488b0074286f2a53096c7a2ef64da30773bf27f5094539a6474d54ed4ace530"
# Coordinates in a three-times magnified detail at original pixel [1648, 1034].
# The two observed spirals are independently traced. The top canal joins them.
TRACES = {
    "left volute": [(184,71),(146,73),(107,76),(82,81),(66,92),(54,111),(49,134),(51,157),
                    (58,181),(72,199),(93,211),(119,217),(144,215),(164,205),
                    (179,189),(182,169),(178,149),(168,131),(153,116),(134,108),
                    (116,108),(101,114),(90,127),(86,143),(90,162),(101,179),
                    (118,189),(135,190),(147,181),(153,169),(151,155),(144,145),
                    (134,140),(120,139),(111,146),(113,156),(122,162),(129,156)],
    "right volute": [(178,69),(222,67),(265,63),(300,60),(320,58),(342,63),(362,78),
                     (377,98),(386,122),(389,145),(384,166),(373,185),(354,199),
                     (334,207),(310,207),(290,201),(273,187),(264,169),(261,149),
                     (264,128),(272,111),(285,101),(300,97),(318,96),(335,101),(348,112),
                     (356,126),(360,140),(357,153),(347,166),(334,172),(319,172),
                     (306,165),(298,154),(296,142),(300,131),(310,125),(322,124),
                     (332,129),(338,139),(335,148),(326,151),(318,147),(315,141)]
}
EDGE=[(42,114),(48,97),(56,82),(68,70),(83,64),(109,62),(151,61),
      (191,58),(241,56),(278,52),(308,47),(330,47),(349,53),(367,67),
      (383,88),(396,116),(401,141),(396,165),(388,183),(376,197),
      (361,210),(342,218),(323,221),(300,219),(284,212),(266,202),
      (257,198),(249,203),(232,204),(214,207),(196,211),(181,216),
      (162,223),(141,229),(117,229),(96,225),(75,216),(60,203),
      (49,184),(42,163),(39,143),(40,127)]
def native(points):
    return np.asarray(points,dtype=float)/3.+[1648.,1034.]


def trace(core,controls,closed,edge=False):
    uv=native(controls)
    if closed:uv=np.vstack((uv,uv[0]))
    t=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(uv,axis=0),axis=1))]
    s=np.linspace(0,t[-1],max(32,int(t[-1]/.75)),endpoint=not closed)
    path=PchipInterpolator(t,uv)(s)
    delta=np.roll(path,-1,axis=0)-np.roll(path,1,axis=0) if closed else np.gradient(path,axis=0)
    norm=np.column_stack((-delta[:,1],delta[:,0]))
    norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-6)
    offsets=np.arange(-3.,3.01,.25)
    q=path[:,None,:]+offsets[None,:,None]*norm[:,None,:]
    strip=map_coordinates(core,[q[:,:,1],q[:,:,0]],order=1,mode='nearest')
    strip=gaussian_filter(strip,(1.35,2.2),mode=('wrap' if closed else 'nearest','nearest'))
    if edge:
        score=abs(np.gradient(strip,.25,axis=1))-.48*offsets**2
    else:
        # A crest is light against its two shadowed sides. Compare locally
        # along its normal so a change of exposure cannot move the whole coil.
        score=strip-.60*offsets**2
    chosen=offsets[np.argmax(score,axis=1)]
    chosen=gaussian_filter1d(chosen,2.6,mode='wrap' if closed else 'nearest')
    p=path+chosen[:,None]*norm
    return p


def run(photo,output,review=None):
    if hashlib.sha256(photo.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError("Unexpected street photo")
    with Image.open(photo) as im:
        tile=im.convert('RGB')
    image=np.asarray(tile.convert('L'),float)
    core=gaussian_filter(image,.57)
    curves={name:trace(core,xy,False) for name,xy in TRACES.items()}
    edge=gaussian_filter1d(trace(core,EDGE,True,True),1.55,axis=0,mode="wrap")
    # Use isolated, strong consecutive troughs on the viewer-left half of the
    # selected shaft. The hidden back is continued with a rotational estimate.
    rows=np.arange(1170.,1341.,3)[:,None]
    left=1687.+.203*(rows-1170.);right=1769.+.269*(rows-1170.)
    theta=np.linspace(-1.18,.13,450)
    x=(left+right)/2+(right-left)/2*np.sin(theta)
    tone=map_coordinates(core,[np.broadcast_to(rows,x.shape),x],order=1).mean(axis=0)
    residual=tone-gaussian_filter1d(tone,57)
    stations=[]
    for center in [-1.05,-.74,-.34,.06]:
        mask=abs(theta-center)<.075;stations.append(float(theta[mask][np.argmin(residual[mask])]))
    spacing=np.median(np.diff(stations));estimated=int(round(2*np.pi/spacing))
    datum={"shaft_upper_centre_px":[1716.0,1116.0],
           "shaft_upper_left_px":[1679.0,1118.4],"shaft_upper_right_px":[1755.5,1114.1],
           "reference_eye_px":[[1689.0,1086.3],[1756.5,1082.1]],
           "lower_shaft_scan_limits_px":[[1687.,1170.],[1769.,1170.],[1721.7,1341.],[1815.,1341.]],
           "shaft_axis_du_per_dv":.236,"estimated_complete_flute_count":estimated,
           "observed_trough_angles_rad":np.round(stations,5).tolist(),
           "median_trough_spacing_rad":round(float(spacing),5)}
    result={"source_page":"https://commons.wikimedia.org/wiki/File:Zhongfudalou.jpg","photograph_sha256":SOURCE_SHA,
            "credit":"Fayhoo, uploaded 19 January 2015. CC BY-SA 3.0.","source_dimensions_px":[2041,1363],
            "selection":"Viewer-left column of the right-hand interior pair. The photographed half of the capital faces the street. Source includes a pair of involuted scrolls, the horizontal canalis and the neck of a fluted shaft.",
            "scale":datum,"front_silhouette":edge.round(3).tolist(),"scroll_crests":{k:q.round(3).tolist()for k,q in curves.items()},
            "carved_fields":[{"name":"weathered field below the canalis","corners_px":[[1711.0,1075.2],[1732.7,1073.6],[1732.2,1085.7],[1711.1,1087.3]]},
                             {"name":"lower rectangular field","corners_px":[[1714.0,1093.5],[1731.9,1092.0],[1732.3,1100.4],[1714.9,1102.0]]}],
            "horizontal_details":[{"name":"lower channel lip","trace":native([(110,93),(152,91),(196,87),(233,84),(269,83),(303,80)]).round(3).tolist()},
                                  {"name":"middle fillet","trace":native([(190,162),(205,160),(224,158),(244,157),(257,157)]).round(3).tolist()},
                                  {"name":"neck fillet","trace":native([(198,204),(210,201),(229,199),(245,198),(253,199)]).round(3).tolist()}],
            "interpretation":"The rear face, stone projection and angular continuation of hidden flutes are reconstructions. Individual visible scroll crests and the front stone silhouette were fitted to the source photograph."}
    output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    if review:
        box=(1648,1034,1787,1129);out=tile.crop(box).resize((417,285))
        pen=ImageDraw.Draw(out)
        for p,col in [(edge,'#f4d170'),(curves['left volute'],'#58d8cd'),(curves['right volute'],'#8de59b')]:
            vals=(p-box[:2])*3
            if col=='#f4d170':vals=np.vstack((vals,vals[0]))
            pen.line([tuple(v)for v in vals],fill=col,width=1)
        out.save(review,quality=96)
    print(datum,len(edge),[len(v)for v in curves.values()])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--photo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--review',type=Path)
    a=p.parse_args();run(a.photo,a.output,a.review)

