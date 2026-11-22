"""Use two photographs and actual hinge axes to compare the moving leaf tips."""
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"source"))
from gatehouse_upper_windows import openings, leaf_axes
from yongjia_photo_plane import pixel

def build():
    evidence=json.loads((HERE/"upper-casement-reads.json").read_text())
    data=evidence["leaf_edges"]
    readings=json.loads((HERE/"readability-of-moving-edges.json").read_text())
    row=next(i for i in openings() if i["key"]=="right")
    width=(row["right"]-row["left"])/2-.026
    cases=[]
    for i,entry in enumerate(data.values()):
        origin,d,n=leaf_axes(row,i)
        for camera in ("center15-upper","west15-upper"):
            for z,uv,tag in zip([row["top"]-.030,row["bottom"]+.028],entry[camera],["top","bottom"]):
                status=readings[camera][("left" if i==0 else "right")+"_"+tag]
                original=uv; uv=status["native_px"]
                corner=origin+d*width+n*.002+np.array([0.,0.,z])
                proj=pixel(corner,camera)
                cases.append({"hinge_side":["left","right"][i],"corner":tag,"camera":camera,"first_reading_px":original,"observed_px":uv,"admitted":status["admitted"],"observation_note":status["reason"],"physical_tip_xyz_m":corner.tolist(),"projected_px":proj,"native_error_px":float(np.linalg.norm(np.subtract(proj,uv)))})
    errors=[x["native_error_px"] for x in cases if x["admitted"]]
    return {"state":"December 2015","measured_feature":"Outer free edges of two turned glazed leaves, not the fixed surrounding stone.",
            "uncertainty":"Near-vertical painted frames and branches give a weaker edge on the right leaf, particularly the lower corner in the west station. Leaf thickness and exact hardware are unresolved.",
            "admitted_corners":len(errors),"median_px":float(np.median(errors)),"largest_px":max(errors),"reprojections":cases}

if __name__=="__main__":
    x=build();(HERE/"casement-tip-agreement.json").write_text(json.dumps(x,indent=2)+"\n")
    print(x["median_px"],x["largest_px"])
