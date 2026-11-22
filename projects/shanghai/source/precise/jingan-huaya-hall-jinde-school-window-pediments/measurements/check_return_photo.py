"""Compare the neighbouring bay on both floors with pixels observed in the 2016 oblique photograph."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
M=Path(__file__).resolve().parent
sys.path[:0]=[str(M.parent/'source'),str(M.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
import pediment_windows as frames,visible_wall_and_bay as wall
from glb_triangles import SerialScene

# Each detail was digitised in a proportional crop of the same original 2867 × 4019 frame.
# (origin, original width, scaled width, detail, observed region, expected materials).
CROPS=[([1425,150],1450,650,[
 ('timber around narrow glazed opening',[(112,287),(112,429),(193,330),(209,268),(207,398)],[wall.RED]),
 ('upper glazed opening',[(130,285),(130,360),(138,395),(177,289)],[wall.GLASS]),
 ('round crown pale relief',[(147,164),(152,142),(91,141),(103,121),(210,122),(245,176)],[wall.LIGHT]),
 ('narrow sill mould',[(82,487),(159,504),(208,509)],[wall.LIGHT]),
 ('notched apron',[(122,520),(217,540)],[wall.LIGHT]),
 ('far outer opening red shutter',[(388,481),(391,521),(397,567),(364,486)],[wall.RED]),
 ('plaster between openings',[(255,277),(248,353),(256,448)],[wall.FIELD,wall.LIGHT]),
 ('architrave of projecting wall',[(169,15),(216,14)],[wall.LIGHT,wall.SHADE])]),
 ([1400,1790],1410,650,[
 ('two shutter face',[(155,253),(191,269),(151,341),(218,228)],[frames.BLADE,frames.FRAME,frames.DARK]),
 ('near carved gable',[(173,93),(201,89),(153,77),(204,44)],[frames.STONE,frames.EDGE,frames.BED]),
 ('two vertical surrounds',[(94,218),(98,310),(274,236),(282,329)],[frames.STONE,frames.EDGE,frames.BED]),
 ('forward panel stone surround',[(457,201),(474,454),(450,272)],[frames.STONE,frames.EDGE,frames.BED,wall.FIELD]),
 ('fluted apron',[(101,578),(270,586),(421,589)],[wall.FIELD,wall.LIGHT]),
 ('facing below window',[(301,612),(275,624)],[wall.FIELD,wall.LIGHT])])]
def check(path):
    camera=json.loads((M/'2016-two-window-cameras.json').read_bytes())['oblique']
    p=np.array(camera['P']);eye=-np.linalg.solve(p[:,:3],p[:,3]);scene=SerialScene(path);rows=[]
    for base,full,height,data in CROPS:
        for feature,pixels,materials in data:
            for xy in pixels:
                uv=np.array(base)+np.array(xy)*full/height
                ray=np.linalg.solve(p[:,:3],[*uv,1]);hit=scene.ray(eye,ray,50.);actual=hit['material']if hit else None
                rows.append(dict(feature=feature,native_pixel=uv.tolist(),observed_materials=materials,actual=actual,matched=actual in materials,hit=hit))
    return dict(sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),exposure_sha256=camera['sha256'],direct_matches=sum(v['matched']for v in rows),count=len(rows),measurements=rows)
if __name__=='__main__':
    record=check(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(record,ensure_ascii=False,indent=1)+'\n');print(record['direct_matches'],record['count'])
