"""Project 2020 sign corners and letter extents from the two square street views.

The original views are used for measurement only. Their projective transforms,
manual readings, and the result are small enough to reproduce without imagery.
"""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
def read_json(path):
    return json.loads(path.read_text())

def solve_signs(views, cameras):
    result = {}
    for side, view in views.items():
        base = np.array(cameras["stations"][view["reference"]]["projection"])
        projection = np.linalg.solve(view["to_reference"], base)
        def on_face(u, v, y):
            h = np.column_stack((projection[:,0], projection[:,2], projection[:,3]+y*projection[:,1]))
            q = np.linalg.solve(h, [u,v,1.])
            return (q[:2]/q[2]).round(5).tolist()
        features = {}
        for key, item in view["boards"].items():
            features[key] = [on_face(u,v,item["face_y_m"]) for u,v in item["corners_uv"]]
        letters = []
        for board, char, (l,t,r,b) in view["glyphs"]:
            y = view["boards"][board]["face_y_m"] - .0015
            u,v = (l+r)/2,(t+b)/2
            cx,cz = on_face(u,v,y)
            width = abs(on_face(r,v,y)[0]-on_face(l,v,y)[0])
            height = abs(on_face(u,t,y)[1]-on_face(u,b,y)[1])
            letters.append(dict(board=board, text=char, center_xz_m=[cx,cz], width_m=round(width,5), height_m=round(height,5)))
        result[side] = dict(boards=features, letters=letters)
    return result

if __name__ == "__main__":
    path = ROOT/"measurements/gatehouse-sign-readings.json"
    source = read_json(path)
    result = solve_signs(source["views"],read_json(ROOT/"measurements/yongjia-street-cameras.json"))
    (ROOT/"measurements/gatehouse-sign-positions.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
