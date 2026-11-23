from pathlib import Path
import json
from math import dist
s=Path(__file__).resolve().parent
reg=json.loads((s.parent/'measurements/two-photograph-registration.json').read_bytes())
def camera(name,label,eye,target,span,w=900,h=720):
    return dict(name=name,label=label,eye=eye,target=target,width_m=span,width=w,height=h)
views=[camera('overview','院门与门后住宅',[-7.8,-13,7.3],[.55,3.65,2.58],14.8)]
for name,label in [('press-2023','亦村四号院门 · 正面照'),('shangguan-2021','钢窗及三孔山墙 · 斜位照')]:
    v=reg['stations'][name];w,h=v['layout'];eye=v['eye_m'];target=v['target_m'];span=dist(eye,target)*w/v['focal_px']
    views.append(camera(name,label,eye,target,span,w,h))
views.extend([
 camera('gate-front','两扇锈铁门与门柱',[0,-7,1.64],[0,0,1.24],4.65),
 camera('number-four','右柱四号门牌',[1.91,-1.54,2.19],[1.46,-.04,1.995],.59),
 camera('gable-vents','山墙上的三孔',[.98,3.66,5.32],[.92,8.12,4.84],2.05),
 camera('steel-window','钢窗与外机',[.16,3.1,3.97],[1.11,8.04,3.91],2.92),
 camera('gate-latch','门扇包边与搭扣',[1.94,-2.18,1.51],[.65,0,1.13],1.45),
 camera('garden-section','院门与山墙的间距',[12.7,-6.6,7.65],[.4,3.95,2.60],14.7)])
(s/'cameras.json').write_text(json.dumps(views,ensure_ascii=False,indent=2)+'\n')
