# 恒业里江西中路115号泗泾路转角

上海市房管局第三批优秀历史建筑3A015恒业里登记江西中路135弄1至11号、江西中路115至147号单号及泗泾路10至24号双号。本次取两路交会处西北街块的东南角。2014年1月29日的照片同时拍到店面上方的“115”和江西中路蓝色路牌。放大照片可见路牌有独立支杆，两侧砖墙的建模范围止于建筑本体。115号两条独立单位地址落在同一建筑轮廓内。地图以“135弄1至13号”定位恒业里旧址，落入另一处面，弄内各宅另行核对。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [2014年现场照片，Antigng，CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:恒业里.jpg) · [原始门牌与足印记录](reference-review.json)

2019年5月20日从泗泾路向街角看，可以数出底层连续浅券窗和石色窗台，上方两排窗以红砖浅券收头。转角为没有中央开窗的弧形灰砖墙，层间红砖线带与檐线绕过街角。2021年1月12日的路口照片还显示江西中路临角的长方窗洞和门洞。2014年的店招、广告遮盖了底层的一部分，到2019年角部已出现连续灰砖墙身。街墙采用2019年与2021年都能辨认的形制。[2019年泗泾路方向](https://mapsv0.bdimg.com/?qt=sdata&sid=09000300121905200935155347I&pc=1) · [2021年路口方向](https://mapsv0.bdimg.com/?qt=sdata&sid=09000300122101121150143417I&pc=1) · [各张照片位置及原图分片](reference-review.json)

底图建筑2354占地约957平方米，与OpenStreetMap建筑378107197的轮廓交并比为97.66%。地图源整栋给高19.2米，OpenStreetMap登记六层。街面照片清楚显示底层及两排上层窗。沿街取靠圆角的短段，保留楼后原体量。屋顶全形、弄内住宅、院落、通道、其余门牌段和室内仍待另外的可靠图证。层高、转角半径、窗洞尺寸与墙身进深按照片比例估计。[OpenStreetMap建筑](https://www.openstreetmap.org/way/378107197) · [模型范围及邻楼排重](reference-review.json)

## 可见街墙与初稿

以两条底图街线的交点定向，泗泾路侧取7.26米，江西中路侧取6.90米，转角半径按照片估为1.38米。两侧各做三开间上层窗，保留中央弧面实墙。灰砖、红砖和错缝砂浆的贴图从参数生成。同一街角的近远两档各接受76条实际三角面射线，覆盖玻璃、窗框、券楣、突出腰线、圆砖实墙和檐上净空。[初稿视图](corner-study.jpg) · [初稿射线](corner-study-rays.json) · [街墙源码](source/hengye_corner.py) · [砖纹及贴图坐标](source/brickwork.py)

2018、2021和2024年发布的三版航片中，两条街的屋面边线连续。2024年图层还能看清后排平行屋脊及其间受阴影遮盖的开敞缝隙。局部街墙止于檐口，后部保留底图轮廓。航片年份取自图层发布记录。[三个图层的取图地址及散列](roof-reference.json) · [初稿落位与近远两个网格](corner-study.json)

## 重建

从上海项目目录运行以下命令。制作程序写入原始、网页、远景三个GLB及可编辑Blender文件。提供源码的原创街墙几何与程序生成的砖纹采用仓库MIT许可。照片按各来源登记的授权署名。

```sh
python source/precise/huangpu-hengye-li-jiangxi-corner/source/brickwork.py
python source/precise/huangpu-hengye-li-jiangxi-corner/source/build_model.py \
  --out assets/models/candidates/huangpu-hengye-li-jiangxi-corner \
  --audit data/audit/hengye-li-jiangxi-corner-v1 \
  --blender blender --gltfpack gltfpack --oidn oidnDenoise
```
