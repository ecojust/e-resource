"""Build nine viewing cameras including the full courtyard and portrait entrance survey stations."""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).absolute().parent

def photograph(name, label, key, entry, y=0):
    center, rotation, intrinsics = map(np.asarray, (entry['C'], entry['R'], entry['K']))
    distance = (y - center[1]) / rotation[2, 1]
    width, height = entry['size']
    return dict(name=name, label=label, eye=center.tolist(), target=(center + rotation[2] * distance).tolist(),
                world_up=(-rotation[1]).tolist(), width_m=float(width * distance / intrinsics[0, 0]),
                width=width, height=height, reference=key)

def view(name, label, eye, target, width):
    return dict(name=name, label=label, eye=eye, target=target, width_m=width, width=1024, height=680)

def views():
    wide=json.loads((HERE/'court-cameras.json').read_bytes())['views']
    close=json.loads((HERE/'entrance-cameras.json').read_bytes())['close_view']
    return [view('overview','主楼与西侧翼全景',[-12,-39,9.5],[-.9,1.2,8.9604],35.0),
            photograph('photo-court','2015年庭院原机位','Fayhoo commons',wide['commons']),
            photograph('photo-entrance','2018年竖幅门廊原机位','Gao 06',close,-1.08),
            view('canopy','拱形雨篷与双吊灯',[-3.9,-9.1,3.65],[-1.06,-1.7,4.10],5.2),
            view('panels','门旁分块金属铭牌',[-4.05,-5.9,3.0],[-3.23,-.05,2.81],4.9),
            view('right-lion','右侧石狮与绣球',[-.25,-5.1,.96],[.40,-2.49,.73],2.1),
            view('balustrades','阳台镂空栏板',[-8.8,-12.5,6.9],[-6.8,-1.15,5.85],7.0),
            view('west','西侧翼与转角窗',[-24,-14,8.2],[-9.3,2.8,7.7],18.2),
            view('roof','红瓦交接与山花',[-16,-24,24],[-1.3,2.0,13.2],29.2)]

if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(views(),ensure_ascii=False,indent=2)+'\n')
