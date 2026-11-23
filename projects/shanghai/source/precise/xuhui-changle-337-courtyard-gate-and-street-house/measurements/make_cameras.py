"""Build three registered photographic views and six study cameras of the gate and street house."""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent

def original(cameras, key, name, label):
    camera = cameras[key]
    eye = np.asarray(camera['eye'])
    rotation = np.asarray(camera['R'])
    width, height = camera['size']
    distance = -eye[1] / rotation[2,1]
    target = eye + rotation[2] * distance
    intrinsic = np.asarray(camera['K'])
    return {'name':name,'label':label,'eye':eye.tolist(),'target':target.tolist(),
            'width_m':distance * width / intrinsic[0,0],'width':width,'height':height,
            'world_up':(-rotation[1]).tolist(),'reference':key,
            'pixel_aspect_y':1.0,'sensor_fit':'HORIZONTAL','shift_x':0.0,'shift_y':0.0,
            'principal_point_px':[float(intrinsic[0,2]),float(intrinsic[1,2])]}

def study(name, label, eye, target, field, size):
    return {'name':name,'label':label,'eye':eye,'target':target,'width_m':field,
            'width':size[0],'height':size[1]}

def make():
    cameras = json.loads((HERE/'street-cameras.json').read_bytes())['cameras']
    cameras.update(json.loads((HERE/'gate-station-cameras.json').read_bytes())['cameras'])
    return [
        study('overview','临街住宅、退翼与337号院门',[9.7,-27.0,9.25],[5.42,1.40,5.21],25.3,(1100,690)),
        original(cameras,'2017','photo-2017','2017年夏季临街实照机位'),
        original(cameras,'2015-12-east','photo-2015-east','2015年冬季沿街侧向机位'),
        original(cameras,'2101g','photo-2021-gate','2021年冬季院门机位'),
        study('casements','绿窗开扇与下层倾板',[2.1,-8.80,3.42],[1.34,0.,2.69],6.75,(970,685)),
        study('clay-eaves','两座低檐、斜脊与椽头',[-3.65,-13.5,10.55],[3.92,1.32,6.31],15.4,(1040,668)),
        study('upper-storey','后起高层的白窗与外开绿扇',[4.28,-9.05,9.44],[2.55,4.43,8.68],8.18,(960,675)),
        study('street-number','337号绿牌、柱帽与双扇铁门',[11.37,-5.72,2.36],[12.57,-.16,1.28],4.26,(900,665)),
        study('inset-wing','退进窗墙、百叶与落水斗',[6.84,-5.81,5.15],[7.52,2.15,3.92],7.47,(980,670)),
    ]
if __name__ == '__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
