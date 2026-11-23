"""Build the courtyard's two registered photographic cameras and seven study views."""
from pathlib import Path
import argparse
import json
import numpy as np

def photograph(key, label, registered):
    c=registered["cameras"][key]
    center=np.asarray(c["C"])
    rotation=np.asarray(c["R"])
    target_distance=-center[1]/rotation[2,1]
    target=center+target_distance*rotation[2]
    return {"name":"photo-"+("2013" if key=="04" else "2016"),"label":label,
            "eye":center.tolist(),"target":target.tolist(),
            "width_m":target_distance*c["width"]/c["f"],"width":c["width"],"height":c["height"],
            "world_up":(-rotation[1]).tolist(),"reference":"Gao88 #04" if key=="04" else "masa3594 #43034625",
            "pixel_aspect_y":1.0,"sensor_fit":"HORIZONTAL","shift_x":0.0,"shift_y":0.0,
            "principal_point_px":[c["cx"],c["cy"]]}

def study(key,label,eye,target,width,size):
    return {"name":key,"label":label,"eye":eye,"target":target,"width_m":width,
            "width":size[0],"height":size[1]}

def make(registered):
    return [
        study("overview","后排1230号院向立面",[.9,-22.5,6.1],[2.1,0,6.55],20.8,[1000,760]),
        photograph("04","2013年院内1230号近照",registered),
        photograph("25","2016年院内斜向全景",registered),
        study("entry","台阶与内门",[-1.20,-8.1,2.18],[0,.5,2.05],4.55,[920,790]),
        study("plaque","绿色门牌与红箱",[1.58,-3.4,2.45],[1.30,0,2.28],1.45,[850,710]),
        study("balconies","四层叠阳台",[7.0,-14,6.35],[5.55,.15,6.8],10.55,[780,1000]),
        study("openwork","灰栏透孔与绿色滴水",[7.35,-6.45,4.27],[5.48,0,4.47],4.65,[940,640]),
        study("court-windows","院窗与两道灰带",[-.9,-11.5,5.65],[.12,0,6.15],8.15,[850,825]),
        study("upper-eave","上层玻璃围合与檐底",[9.4,-9.0,11.65],[4.18,-.03,11.34],9.35,[1000,640])]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    m=Path(__file__).resolve().parent
    p.add_argument("--registered",type=Path,default=m/"registered-rear.json")
    p.add_argument("--output",type=Path,default=m.parent/"source/cameras.json")
    a=p.parse_args()
    a.output.write_text(json.dumps(make(json.loads(a.registered.read_text())),indent=2,ensure_ascii=False)+"\n")
