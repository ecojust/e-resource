"""Verify the photographed doors, transom, sun-room glazing and garden approach in every GLB."""
from argparse import ArgumentParser
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

ROOT=Path(__file__).resolve().parent
first_contact=runpy.run_path(str(ROOT.parent/'xiaotaoyuan-prayer-hall-v1/check-openings.py'))['first_contact']
GLASS='shaded courtyard glass'
WOOD='brown painted joinery'
IRON='dark garden ironwork'
ROOF='red ochre clay tile'
PLASTER='ochre cream roughcast'
# Depth is local north for southern rays, local east for eastern rays, and
# height above the lane for roof rays. The glass must be the first visible hit.
SAMPLES=[
 ('93 enamel background','south',-.727,2.32,'green enamel house number',-.075,-.060),
 ('9 upper stroke','south',-.681,2.406,'pale ceramic numerals',-.086,-.074),
 ('3 upper stroke','south',-.587,2.403,'pale ceramic numerals',-.086,-.074),
 ('left shutter panel','south',-.35,1.18,WOOD,.08,.11),
 ('right shutter panel','south',.37,1.18,WOOD,.08,.11),
 ('door meeting stile','south',0,1.25,WOOD,.04,.07),
 ('left door glass','south',-.35,1.92,GLASS,.14,.18),
 ('transom open light','south',.03,2.51,GLASS,.12,.15),
 ('transom diamond bar','south',.17,2.42,WOOD,.06,.09),
 ('heritage marker face','south',-1.10,1.94,'patinated commemorative plaque',-.060,-.041),
 ('shaped marker top','south',-1.10,2.204,'patinated commemorative plaque',-.060,-.041),
 ('left casement glass','south',-1.79,1.37,GLASS,.055,.085),
 ('right casement glass','south',1.81,1.37,GLASS,.055,.085),
 ('left casement sill','south',-1.68,.64,'painted off-white sill',-.165,-.125),
 ('west canopy corbel','south',-.79,2.65,WOOD,-.40,-.35),
 ('canopy flashing','south',.68,2.97,'lead-grey flashings',-.96,-.92),
 ('projecting bay apron','south',.53,3.56,PLASTER,-.76,-.72),
 ('front bay glass','south',.43,4.75,GLASS,-.71,-.68),
 ('front bay centre stile','south',0,4.68,WOOD,-.75,-.71),
 ('west angled bay glass','south',-1.26,4.46,GLASS,-.37,-.32),
 ('east angled bay glass','south',1.29,4.46,GLASS,-.31,-.25),
 ('gable render','south',.18,7.39,PLASTER,-.28,-.24),
 ('gable rake tile','south',.03,7.93,ROOF,-.43,-.39),
 ('window in bay roof','top',.23,-.52,GLASS,5.98,6.01),
 ('east roof pitch','top',2.67,1.13,ROOF,6.55,6.62),
 ('ridge cap','top',2.6,3.40,ROOF,7.50,7.56),
 ('west garden post','south',-1.18,1.77,IRON,-2.25,-2.20),
 ('east garden post','south',1.18,1.70,IRON,-2.25,-2.20),
 ('house visible above the fence','south',-2.79,1.53,PLASTER,-.02,.02),
 ('open garden leaf','top',1.33,-1.19,IRON,1.24,1.29),
 ('lowest step','east',-.68,.08,'pale granite steps',.79,.84),
 ('clear walk from gate','top',0,-1.40,None,0,0),
 ('horizontal iron railing','south',1.79,1.08,IRON,-2.23,-2.18)]


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--report',default=ROOT/'opening-rays.json',type=Path)
    a=parser.parse_args();variants=[]
    for r in json.loads((a.work/'delivered-decode.json').read_bytes()):
        triangles=np.fromfile(r['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        tags=np.fromfile(r['triangle_material_ids_file'],np.uint16);results=[]
        for name,view,x,z,expected,low,high in SAMPLES:
            mat,depth,normal=first_contact(triangles,tags,r['material_names'],view,x,z)
            assert mat==expected and (mat is None or (low<=depth<=high and normal>.01)),(r['variant'],name,mat,depth,normal)
            results.append(dict(feature=name,view=view,coordinates_m=[x,z],first_depth_m=depth,material=mat,outward_normal_dot=normal))
        variants.append(dict(variant=r['variant'],sha256=r['sha256'],rays=results))
    a.report.write_text(json.dumps({'model_id':'huangpu-feng-zikai-riyue-lou','checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants},indent=2)+'\n')
    print(len(variants)*len(SAMPLES),'visible surfaces or empty passages checked')

if __name__=='__main__':main()
