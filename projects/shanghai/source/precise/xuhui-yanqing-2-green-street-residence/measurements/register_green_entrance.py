"""Compare the green grille in the documented June 2015 and September 2017 images.

The four metal frame corners determine the plane transfer. All other points
remain independent measurements in both images.
"""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np

HERE=Path(__file__).resolve().parent
CONTROLS=[
 ('overlight outer west corner',[1127.,1036.],[268.0,192.5]),
 ('overlight outer east corner',[1268.,1036.],[450.0,191.2]),
 ('outer southeast foot',[1268.2,1263.5],[441.7,506.5]),
 ('outer southwest foot',[1127.3,1263.2],[265.6,482.2]),
]
INDEPENDENT=[
 ('west end of transom',[1127.5,1073.],[268.2,243.7]),
 ('east end of transom',[1267.8,1073.],[448.4,247.0]),
 ('west edge of dark arch below key',[1196.,1060.],[355.2,226.3]),
 ('upper left of pale keystone',[1184.4,1015.6],[352.0,168.0]),
 ('upper right of pale keystone',[1208.,1016.2],[378.3,167.0]),
 ('bottom left of intercom housing',[1243.2,1147.2],[402.4,349.1]),
 ('top right of intercom housing',[1254.5,1119.1],[418.7,313.2]),
 ('west end of midsection below notice',[1147.7,1189.4],[294.6,395.7]),
 ('lower-right corner of the lock panel',[1261.7,1189.2],[431.8,404.0]),
]


def homography(correspondences):
    mat=[]
    for _,(x,y),(u,v) in correspondences:
        mat.extend(([x,y,1,0,0,0,-u*x,-u*y,-u], [0,0,0,x,y,1,-v*x,-v*y,-v]))
    h=np.linalg.svd(mat,full_matrices=True)[2][-1].reshape(3,3)
    return h/h[2,2]


def main():
    h=homography(CONTROLS)
    measured=[]
    for n,a,b in INDEPENDENT:
        q=h@[*a,1];q=q[:2]/q[2]
        measured.append(dict(feature=n,source_2015=a,observation_2017=b,
                             transferred_2017=q.tolist(),error_pixels=float(np.linalg.norm(q-b))))
    output=dict(
        address='上海市徐汇区延庆路2号沿街住宅',
        register=dict(code='5D067',scope='延庆路4弄（2–44号）、延庆路2–6号（双号）',
          url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html'),
        photos={
          '2015':dict(author='Fayhoo',date='2015-06-21',dimensions=[2144,1424],license='CC BY-SA 3.0',
                      page='https://commons.wikimedia.org/wiki/File:Yanqinglu_2_Hao_Zhuzhai.JPG',
                      sha256='de0b409edfd8501a759396472b73308bf1d0521a96906d655a4fd0c812aac263'),
          '2017':dict(provider='Baidu public street panorama',station='09000300121709041034411551Y',
                      date='2017-09-04',original_station_metadata='https://mapsv0.bdimg.com/?qt=sdata&sid=09000300121709041034411551Y',
                      dimensions=[840,560],heading=225,pitch=0,horizontal_fov=52,tile_level=4,
                      rendered_reference_sha256='6e634166e99338e8f9c688d3375d30457a3877933580d9d6a3a1ca2701406e94',
                      rights='街景仅作比对。此处公布投影参数与原创读数。')},
        controls=CONTROLS,homography_2015_to_2017=h.tolist(),held_out=measured,
        errors_2017_px={'median':float(np.median([a['error_pixels'] for a in measured])),
                        'max':float(max(a['error_pixels'] for a in measured))},
        observation='两期均有墨绿矩形外框、栏杆上亮、浅色弧券与梯形楔饰、中腰横百叶、右侧门铃。2015年中央挂白底红黄公告，2017年在同一块栏杆挂城市天际线图。重建保留固定铁件、两块2号绿牌和东端小窗。两块牌的下款只可辨三组浅色印迹，未誊录文字。',
        depth_limits='门环形券及对讲器与格栅不在完全同一平面。独立斜站的偏差包括景深视差和街景拼接；两期像点不能独立测定全部深度。东端窄窗上部左角受空调遮挡。',
        projection_file_sha256=sha256((HERE/'2015-street-camera.json').read_bytes()).hexdigest())
    (HERE/'fixed-entrance-2015-2017.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(output['errors_2017_px'])

if __name__=='__main__':
    main()
