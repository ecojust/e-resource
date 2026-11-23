# 襄阳南路313号修缮后住宅

这幢三层平顶住宅位于襄阳南路东侧、永嘉路南侧的313号院内。上海市第五批优秀历史建筑登记号为5D103，施工单位记载建筑面积364平方米。2014年街照及2015、2020年街景可分别读到313号院门与旁边的311号门牌。三处临街窗位的交会离城市原户3304对应墙面约0.11、0.26和0.13米。院门旁的乔家栅门面属于另一处实体。[资料与许可](SOURCES-LICENSE.md) · [门牌和城市原户对照](measurements/836-3304-identity.json)

| 方位 | 可以在模型中查看的部分 |
|---|---|
| 南院 | 凸墙四扇二十格窗、白色窗台和圆形外机。中央下层百叶门的两侧墙面各有退进，左侧可见玻璃与开启的百叶扇。相邻退进窗墙有七处开口、钢阳台、交叉栏杆、波纹棚、裙边篷及四台外机。 |
| 北院 | 三扇上层窗、两道半透明青色雨篷和挑出的金属花架。中层包含外开窗、窄窗、落水管与挂脚，凸翼旁只制作照片露出的窗框、窄格和挂钩。 |
| 朝街西墙 | 三个相接的窗面及一段短斜墙。中层主窗为三扇五行，两樘窄窗沿转折墙面后退。上层仅制作街景中可辨认的两樘窗、紫色遮棚、落水管和高低檐口。 |
| 屋顶与东墙 | 保留现有三层混凝土平顶、折形外边、女儿墙和东侧凸翼。西侧凸段较高，测得街面至檐约12.20米，北侧落管上角约11.33米。东侧门窗和室内布局缺少可靠照片。 |

原修缮照片为580×380像素，两处院面分别拟合相机。用原地块11个折点、2019年航片屋缘和西面多站街景将两面落入同一东、北、上坐标系。坐标原点为东经121.4535580°、北纬31.2106021°，街道路面为竖向零点。院内隐蔽地坪沿用估计标高。施工照片的局部高度按街景复核的层距乘1.08，再相对街面上移1.43米。树木遮住的窗脚、外机支架深度、衣物后方及女儿墙厚度均含估计。[摄影机位](measurements/courtyard-cameras.json) · [城市平面与院面变换](measurements/3304-local-footprint.json) · [跨站高度控制](measurements/street-height-controls.json)

近景含645个闭合构件、23,156个三角形。远景含570个闭合构件、15,636个三角形。从南院拍摄点回看，两档均能逐格命中20片玻璃，覆盖四扇凸窗、附近外机、窗台、门篷及百叶的25束测试全部直接命中。退进墙另有24处直接命中，门侧百叶与水管另有9处。钢阳台的21束中，20束命中指定表面，一束先碰到棚下钢檩。北面46处抽查均在原图1像素内，其中43处直接命中。西墙的50处跨站检查保留厂商原姿态与双点校正两种结果，各有48处与49处位于所列容差内。[大窗读数](measurements/large-window-readings.json) · [西墙原像抽查点](measurements/street-window-photo-probes.json)

从仓库根目录执行以下命令，就能生成两档原始GLB并检查构件的有向闭合边和正体积。构建需要Python、NumPy、Pillow及Shapely 2.1或更新版本。重算相机参数另需SciPy。

```sh
model=projects/shanghai/source/precise/xuhui-xiangyang-313-restored-courtyard-fronts
python -B "$model/measurements/check_mesh.py" /tmp/xiangyang313
python -B "$model/measurements/check_large_window.py" /tmp/xiangyang313/full-source.glb /tmp/xiangyang313/window-rays.json
python -B "$model/measurements/check_street_windows.py" --south-attitude /tmp/xiangyang313/full-source.glb /tmp/xiangyang313/west-rays.json
```
