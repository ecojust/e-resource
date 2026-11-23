"""Test native west-return image rays on a supplied GLB; keep both photographic dates distinct."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from wing_frame import WingFrame

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Registration landmarks in wing-observations.json are excluded from these rays.
MARKS={
    'design':{
        'near lower pane upper':([121,212],'desaturated window glass'),
        'near lower pane centre':([121,217],'desaturated window glass'),
        'near lower pane bottom':([121,224],'desaturated window glass'),
        'rear window left dark division':([93,209],'dark oak framing'),
        'rear window right dark division':([96,217],'dark oak framing'),
        'rear window jamb':([91,210],'dark oak framing'),
        'near wall under the band':([130,219],'warm garden brick'),
        'intervening brick panel':([106,214],'warm garden brick'),
        'full-height post in the step':([102.5,212],'dark oak framing'),
        'post left of nearer ground window':([112,214],'dark oak framing'),
        'first upper panel':([136,192],'cream lime infill'),
        'second upper panel':([120,196],'cream lime infill'),
        'third upper panel':([110,195],'cream lime infill'),
        'larger dormer centre':([114,167],'desaturated window glass'),
        'larger dormer upper front':([117,156],'desaturated window glass'),
        'larger dormer cheek':([127,160],'warm garden brick'),
        'larger dormer slates':([143,138],'reddish plain tile'),
        'smaller dormer centre':([92,167],'desaturated window glass'),
        'smaller dormer cheek':([100,168],'warm garden brick'),
        'smaller dormer slates':([104,146],'reddish plain tile'),
    },
    'album':{
        'left in small low window':([347,604],'desaturated window glass'),
        'centre in small low window':([353,612],'desaturated window glass'),
        'base of small low window':([351,616],'desaturated window glass'),
        'left light panel':([331,590],'cream lime infill'),
        'right light panel':([373,589],'cream lime infill'),
        'solid wall beyond historic dark opening':([378,609],'warm garden brick'),
        'hip dormer dark face':([350,551],'desaturated window glass'),
        'hip dormer centre':([354,555],'desaturated window glass'),
        'hip dormer right cheek':([373,551],'warm garden brick'),
    }
}

def inspect(mesh):
    frame=WingFrame()
    scene=runpy.run_path(str(HELPER))['SerialScene'](mesh)
    out={'mesh_sha256':scene.asset['sha256'],'camera_sha256':hashlib.sha256((HERE/'wing-cameras.json').read_bytes()).hexdigest(),'views':{}}
    for name,marks in MARKS.items():
        cam=getattr(frame,name);hits=[]
        for feature,(point,material) in marks.items():
            hit=scene.ray(cam.C,cam.ray(point),450)
            actual=hit and hit['material']
            hits.append({'native_xy':point,'feature':feature,'photograph_surface':material,'first_material':actual,'matches':actual=='Eves | '+material})
        out['views'][name]={'matched':sum(i['matches'] for i in hits),'tested':len(hits),'first_hits':hits}
    out['historical_difference']='The older single dark opening strikes solid brick between the two reconstructed design windows. The hip dormer face, cheek and the pale timber band persist in the older view. The current wood profiles and colours refer to the design perspective.'
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model',type=Path);parser.add_argument('report',type=Path);a=parser.parse_args()
    result=inspect(a.model);a.report.write_text(json.dumps(result,indent=2)+'\n');print({k:(v['matched'],v['tested'])for k,v in result['views'].items()})
