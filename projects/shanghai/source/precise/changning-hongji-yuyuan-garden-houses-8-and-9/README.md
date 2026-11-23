# 弘基创意国际园——8、9号楼

愚园路1107号的两栋花园住宅隔草坪相望。东侧8号以高烟囱和红砖山墙朝西，西侧9号以浅色拉毛山墙和双柱门廊朝东。项目待办沿用第五批优秀历史建筑名录中的“弘基创意国际园——8、9号楼”，房管局同址条目为“上海长征制药厂”。园内另有红砖大厂房和带独立7号牌的建筑。[市级名录、门牌与原照](measurements/two-numbered-garden-houses.json) · [三维模型](../../../hongji-yuyuan-garden-houses-8-and-9.html)

| 部位 | 模型所采用的观察 |
| --- | --- |
| 8号草坪面 | 四扇长方形窗穿过砖墙和上部粉刷层。独立砖烟道向屋脊收窄，竖排十个金属字母拼成 STEAK HOUSE。三道浅色固定条从字母之间露出。2023年草坪边的绿篱遮住最下方的 E。[十字轮廓](measurements/eight-chimney-lettering.json) |
| 8号入口与侧面 | 红砖低翼有浅色拱券、三幅落地玻璃和深底铜8字。另一侧的平露台装透空菱格栏板，北侧折面门廊邻着削顶山墙，木门、窄侧窗和上层窗分别建模。门廊上方的白底牛形招牌、门楣上的 Ribone Café 和红砖侧墙的店名牌均按原图描摹、分别挤出。[招牌轮廓与原图测点](measurements/eight-cafe-sign-observations.json) 2016年低翼顶上的玻璃搭建在2023年的同角度照片中已拆除。[六个入口视角](measurements/house-eight-entrance-observations.json) |
| 9号草坪面 | 两层共六扇有真实窗洞的窗，凸起的烟道一直通到瓦屋顶。两根方柱托住石色露台，栏杆中央为实心刻边栏板。台下的两扇玻璃木门向后退约3米，两盏壁灯分列门侧，碗形灯悬在廊中。[六窗](measurements/nine-gable-window-survey.json) · [方柱与门](measurements/nine-entrance-portico.json) · [三盏灯](measurements/nine-porch-lamps.json) |
| 9号侧面 | 南侧三个山墙投影的间距和进深不同，角上挂铜9字，最远一道山墙下可见拱形入口。北侧两处突出体也各有独立窗洞，其中较大屋顶前又伸出一道窄山墙。[南面双照](measurements/nine-south-gables-two-oblique-views.json) · [门牌三面定位](measurements/nine-brass-number-plaque.json) · [北面两站互证](measurements/nine-north-windows-and-stepped-gables.json) |

## 尺寸与年代

8号和9号临草坪的主山墙分别约宽7.12米、7.27米，墙脚中点相距约26.28米。每栋住宅以自己山墙的左下为原点，局部 X 指向面向房屋时的右手，Y 指向室内，Z 向上。两宅借航片和实景定向，共享以8号山墙左脚为零点的东、北、天坐标。[庭院坐标和面积](measurements/two-house-placement-and-garden-axes.json) · [四期航片与屋脊](measurements/two-house-aerial-ridges-and-epochs.json)

模型采用2023年9月发布的照片所示状态。2015年的9号楼原照、2016年的8号和9号楼照片补充了窗格、烟囱和植物遮挡处的证据。现有地面照片覆盖草坪面、入口和主要侧墙。两栋背面墙脚、部分下层窗台、种植边界以及被檐口遮住的构造按照片比例和航片估计。窗后仅保留可从外部看见的构造。[正面六机位及原始误差](measurements/six-front-cameras.json) · [照片和许可](SOURCES-LICENSE.md)

八号正面照片的屋墙、窗和屋脊集中在同一平面附近，仅靠这些点无法唯一确定焦距和拍摄距离。初次拟合落入对面9号楼内。加入露台压顶、低瓦檐和侧招牌后，另给出一个位于9号楼外步道的机位。原照片与两组参数均可复查。[整庭院机位和各点误差](measurements/courtyard-front-station.json)

## 重建

在本目录运行下列命令可生成原始 GLB、压缩近景和简化远景。Python 源码保留两栋住宅和庭院的构件分组，原始 GLB 按材质合并表面，以供网页加载。打包需要 Node.js 和 gltfpack。

```sh
python measurements/export_checked_model.py full --out output/source
python measurements/export_checked_model.py lod --out output/source
python measurements/package-web-model.py output/source output/models output/audit
python measurements/check-six-front-cameras.py
```

[模型检查](../../../data/audit/hongji-yuyuan-garden-houses-8-and-9-v1/README.md)
