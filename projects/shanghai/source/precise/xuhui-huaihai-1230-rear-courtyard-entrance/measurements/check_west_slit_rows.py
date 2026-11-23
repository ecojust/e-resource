"""Check two original source-image rows across all five visible balcony slots."""
from argparse import ArgumentParser
from pathlib import Path
import json
from check_registered_court import Camera, SerialScene

# Row 328 controls the measured widths. The y=335 row was read separately
# before the final assembled meshes were generated, including the bottom tip.
ROWS={328:[174,181,188,195,202],335:[173,180,187,195,202]}
def check(path):
    scene=SerialScene(path);camera=Camera("25");result=[]
    for y,columns in ROWS.items():
        hits=[]
        for x in columns:
            hit=scene.ray(camera.c,camera.ray((x,y)),75)
            hits.append({"pixel":[x,y],"exact_first_hit":hit,
                         "passes_both_faces":bool(hit and hit['point_enu_m'][1]>.12)})
        result.append({"source_row":y,"role":"width-reading line" if y==328 else "separate lower-tip reading",
                       "through":sum(h['passes_both_faces']for h in hits),"hits":hits})
    return {"asset":scene.asset,"station":"masa3594, 2016-01-20 11:24:36, #43034625","rows":result}
if __name__=='__main__':
    p=ArgumentParser(description=__doc__); p.add_argument("mesh",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    j=check(a.mesh);a.output.write_text(json.dumps(j,indent=2)+'\n')
    print([r['through'] for r in j['rows']])
