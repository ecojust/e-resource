# 中山公园大理石亭

上海市房屋管理局第三批优秀历史建筑 3M026，长宁路780号中山公园内。长宁区的公园史记载，爱斯拉夫人赠建的大理石亭于1935年迁建入园，阶、栏、台、柱、壁及两尊雕像为大理石。工程采用2014年正面照和区政府专题发布的两张不同方向照片。其一为旧照，两张区刊照片的原拍摄年份均待考。[区政府资料](https://www.shcn.gov.cn/col6991/20210301/867422.html) · [Fayhoo 正面原照，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Marble_Pavilion_of_Jessfield_Park.jpg) · [房管局原表](http://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html)

前廊四柱中间跨约等于两侧各一跨之和。后屏有三个贯通的拱孔。两侧雕像有独立的龛壁、一手下垂一手横向弯曲的姿态及若干衣褶，按照各自可辨的轮廓塑形。现况照片的顶部有藤蔓，资料旧照显示梁上密椽之间透空。可辨的重要物件还包括侧石栏、两只皿状花钵以及通往广场的各级石阶。模型的两组色面与法线贴图由程序绘制。放大到脸部或手指时，原照不足以辨明细节。

## 实物尺度与复核

两期航片的阶鼻可辨宽度分别约17.12、19.94米，建模采用18.7±2.1米。四根前柱轴线位于局部横向约−5.28、−2.63、2.63、5.28米。前排柱轴至后屏约4.57米。地理基准为两期台阶定位的中值，平面误差估计为4米。[三站测读和来源](measurements/pavilion-observations.json) · [航片原点、真方位和读数](measurements/terrace-aerial-registration.json) · [原城市三角实射及余量](measurements/terrace-original-city-clearance.json)

首版包括柱廊、开孔石屏、台阶和侧栏。细化版增加了左右两尊独立雕像、椽端斜切、灰色石屏砌缝和浅色大理石纹。在35个未用于拟合相机的照片位置上，对原网、网页解码与远景解码三档分别实射。每档31处直接命中预期构件或透空处，另3处在4个工作像素范围内命中。尚有旧照一点落在墙上，向右15像素才穿过拱洞。旧照缺少另一处同期独立视角，暂保留这个误差。[原照留验点及实际射线程序](measurements/check_pavilion_views.py)

## 本地重建

在仓库的 Python 环境安装 NumPy、SciPy、Shapely 2.1 和 Pillow。于本目录运行下列命令。前两项从测读表重算相机，最后一项生成三张原机位模型图及一张对照图。

```sh
python measurements/fit_pavilion.py measurements/pavilion-cameras.json
python measurements/make_pavilion_cameras.py
python source/marble_finishes.py
python measurements/check_mesh.py /tmp/marble-pavilion
python measurements/check_pavilion_views.py /tmp/marble-pavilion/full-source.glb /tmp/marble-pavilion/controls.json
python measurements/check_nine_cameras.py /tmp/marble-pavilion/full-source.glb /tmp/marble-pavilion/frames.json
python measurements/render_pavilion_views.py /tmp/marble-pavilion/full-source.glb /tmp/marble-pavilion/views --width 512
```

打开[独立模型页](../../../zhongshan-park-marble-pavilion.html)即可切换九个机位、近远网和下载格式。
