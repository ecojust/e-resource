"""Register openings and fixed fittings to the receding south court wall, in metres."""
from pathlib import Path
import json
from register_courtyard import Camera

HERE = Path(__file__).resolve().parent
DEPTH = .6725
# Four samples run from top left clockwise. The balcony hides the bottom of
# its two doors. Their lower limit is the photographed balcony deck.
OPENINGS = {
    'upper-shaded': [(82,28),(149,28),(146,67),(82,67)],
    'upper-open': [(199,32),(244,31),(242,76),(196,77)],
    'upper-east': [(291,30),(334,30),(334,69),(291,70)],
    'balcony-open': [(98,138),(146,138),(140,229),(97,229)],
    'balcony-fixed': [(187,139),(238,139),(234,229),(187,229)],
    'middle-east': [(282,139),(328,139),(328,202),(281,203)],
    'ground-centre': [(174,297),(228,297),(223,376),(169,376)],
}
DEPTH_FITTINGS = {
    'violet head': {'front':[(76,24),(151,24)],'back':[(79,20),(146,18)],'drop_px':5,'depth_m':.36},
    'small scalloped head': {'front':[(274,133),(336,134)],'back':[(277,129),(329,129)],'drop_px':4,'depth_m':.30},
    'cyan head at image top': {'front':[(171,7),(340,7)],'back':[(169,1),(342,1)],'drop_px':0,'depth_m':.37},
    'western rails': {'front':[(59,73),(171,72)],'back':[(60,65),(167,64)],'depth_m':.43},
    'eastern rails': {'front':[(279,78),(347,77)],'back':[(282,69),(344,68)],'depth_m':.32},
}
def registered():
    cam=Camera('case1')
    openings={}
    for name,pixels in OPENINGS.items():
        tl,tr,br,bl=[cam.wall(uv,DEPTH) for uv in pixels]
        bounds=[(tl[0]+bl[0])/2,(bl[2]+br[2])/2,(tr[0]+br[0])/2,(tl[2]+tr[2])/2]
        openings[name]={'corners_px':pixels,'bounds_xz_m':[round(v,4) for v in bounds]}
    return {'view':'case1','native_image_px':[580,380],'setback_m':DEPTH,'openings':openings,
            'fittings':DEPTH_FITTINGS,
            'limits':'Upper and middle frontal glazing and fixed fittings are visible in the contractor photograph. Cloth, plants and wires obscure the lower left, the bottom of the balcony doors and the full extent of the ground-floor opening. The edge of image height limits the small cyan sheet. Bracket depth and the hidden pane edges are approximate.'}
if __name__=='__main__':
    (HERE/'setback-wall-readings.json').write_text(json.dumps(registered(),indent=2,ensure_ascii=False)+'\n')
