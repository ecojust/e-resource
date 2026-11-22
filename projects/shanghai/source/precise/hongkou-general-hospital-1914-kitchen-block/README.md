# 公济医院旧楼东部（1914年后勤楼）

北苏州路190号的历史院址内，天潼路与乍浦路交会处保留了一栋五层红砖楼。1914年12月5日的《北华捷报》记载，George A. Johnson 为院方扩建两栋楼，建造方为 Koo Lan-chow。乔争月在2020年报道中对照旧报与实物，把现存建筑辨认为负责厨房、洗衣及员工用房的后勤楼。上海市第五批优秀历史建筑登记名为“公济医院旧楼东部”，编号 HK-J-030-V。同院修女宿舍、沿苏州河的早期病房与后建酒店各有独立的建筑沿革。[名录原行](measurements/historic-listing.json) · [报道及照片](SOURCES-LICENSE.md)

## 三个可核对的立面

- 北面有两组各五轴钢窗，第三层的三角和弧形石窗楣间置，中间留出石额。底层第一轴是实墙，第六和第七轴是两个入口，其余七轴各有钢窗。东侧突出短墙的底座是整片浅石，居中开双扇门。[底层实照像点](measurements/ground-front-pixels.json)
- 北面十轴与南院四个三角额窗轴有同色石材从二层连到三层。南院另四个平额轴在短石裙下露红砖。窗洞从砖墙和石板中分别切出，能从斜向看出钢窗与墙皮的距离。[石板两侧标点](measurements/stone-window-panel-spans.json) · [钢窗布局](source/sash-layout.json)
- 南院高处悬挑一座长阳台，保留浅色悬臂、外沿和铁栏。屋面沿可见边有密排牛腿和透空瓶栏，并有街角抬高的砖体、中段方砖烟道及一座院侧矮房。石额的中央石面在两张公开照片中均有磨蚀，模型保留表面起伏。[庭院照片记录](measurements/research-plates.json) · [石额配准](measurements/stone-cartouche-registration.json)

## 比例与不确定处

楼体局部坐标以东北街角为原点，X沿天潼路向西，Y指向庭院，Z向上。14个实景视图中的23条视线分别交会七个可辨点。北面两端石角相距约44.62米，东短面在庭院侧的外角约为 X=1.14、Y=11.33米。近街第一段退进位置约在Y=4.95米。用六角折线计算的展示平面面积约498平方米；旧报给出的502平方米原文采用“covered an area”，两者分别保留。[街景交会](measurements/street-and-courtyard-intersections.json)

乔争月的街角图做了建筑透视校正。计算时放开垂直主点，用街角和西端控制长立面，并以可见门槛定地面。戴邹君的庭院图单独用石带与窗框校正，留作检查的主檐在两张照片中均约23.7米。庭院照的西端被邻楼遮挡，模型在名录楼体的展示范围闭合。不同街站的上层角点会有约一米量级的分歧，屋顶背面、阳台局部进深和女儿墙内侧也含估计。没有现场测绘或室内平面图。[街角相机](measurements/camera-fit/qiao-shifted-perspective.json) · [庭院相机](measurements/camera-fit/dai-court-camera.json) · [城市底图交接](measurements/placement-identity.json)

## 重建

从仓库根目录运行，Python 环境及 Blender、gltfpack、OIDN 使用上海项目现有工具链。两条单独导出命令适合修改窗扇或比较远近网格。正式打包入口增加独立重开 Blender、渲染与网格比较。

```sh
cd projects/shanghai/source/precise/hongkou-general-hospital-1914-kitchen-block/source
python hospital_finish.py
mkdir -p output
python build_model.py --output output/gongji-1914-full.glb
python build_model.py --output output/gongji-1914-lod.glb --lod
python build_model.py --help
```

红砖贴图由固定随机种子生成，砖和灰缝的绝对尺寸采用展示估值。下载资产的精确大小、SHA256 和逐项检查结果随对应版本发布。[审核记录](../../../data/audit/general-hospital-1914-kitchen-block-v1/README.md)
