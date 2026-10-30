# 俄罗斯领事馆历史主楼：2010外观参照候选

[独立模型与外围漫游](../../../russian-consulate.html) · [资产清单](../../../assets/models/candidates/hongkou-russian-consulate/manifest.json) · [检查记录](../../../data/audit/russian-consulate-v1/README.md)

依据Baycrest的2010年5月公开照片、虹口旧保护建筑资料与上海地方志制作一件历史主楼外观候选。含浅色墙体、真实矩形与拱形窗洞、线脚壁柱、阳台石栏与柱、曲线山花、红色折坡屋面、拱形老虎窗、塔身与绿色曲顶。照片中的现代邻楼、园内凉亭、岸墙、植被和临时设备不作为本件建筑几何。

## 文献与估计边界

地方志记四层；本件解释为三层立面加坡屋顶层，不证明逐层对应。主楼44×24米、每层4.2米、屋面折点16.8米、主脊18.6米、塔顶30.8米**全部为设计估计，不是史料公布或现场量测**。地图仅有不规则身份轮廓，没有可用高度或分段，本件未挤出地图轮廓，也未进行原址配准。

地方志约10×2米属于阳台，不能代替主楼尺寸。候选将其作为照片近侧一组阳台的设计尺寸，在三处标高重复；这不是三个实物阳台位置均已核验。照片右侧封闭凸窗／阳台的独特体量尚未独立复原，候选该部分仍用简化主体墙面。前侧名称是局部展示方向，不把照片直接认定为文献的正北立面。

窗数、间距、开口尺寸、栏杆数量、山花曲线、阁窗、烟囱、屋顶坡度、塔位和塔顶八分结构、背面及其全部窗网均为估计。深色塔身细条为浅置外观表达，未切成可通行开口。老虎窗罩体向屋内延伸以覆盖真实坡面洞口；近景保留分格窗框、轮廓线和较密石栏，远景减少窗框、曲线细分和石栏数量。两档外包一致。

虹口旧资料称1916年，地方志称民国六年即1917年；百科竣工／开馆日期只是可能解释，不当作已消解差异。1700／1700余平方米用地和3264平方米建筑面积没有用于反推主体长宽。地方志六角形凉亭与照片塔部不能自动视作同一构件；本件没有建园内凉亭。

[逐项来源与许可](source-register.json) · [全部设计参数](design-input.json)。Baycrest照片为CC BY-SA 2.5（https://creativecommons.org/licenses/by-sa/2.5/），仅本地查看，无照片像素、第三方贴图或原图再分发。无开放许可的文字仅短引事实和链接，不复制全文。原创代码与几何MIT；纯色粗糙度材质，无真实墙面PBR扫描、风化和细部雕塑，未伪造徽章文字。

## 复跑

从仓库根目录运行，Python依赖见`source/requirements.txt`，Blender4.3.2与gltfpack1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/hongkou-russian-consulate/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/hongkou-russian-consulate/source/build_model.py --out /tmp/russian
python projects/shanghai/source/precise/hongkou-russian-consulate/source/build_model.py --out /tmp/russian --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/hongkou-russian-consulate/source/build_native.py -- --raw /tmp/russian/hongkou-russian-consulate-raw.glb --out /tmp/russian/hongkou-russian-consulate.blend --previews /tmp/russian-previews
python projects/shanghai/source/precise/hongkou-russian-consulate/source/package_assets.py --raw /tmp/russian/hongkou-russian-consulate-raw.glb --lod /tmp/russian/hongkou-russian-consulate-lod.glb --native /tmp/russian/hongkou-russian-consulate.blend --out projects/shanghai/assets/models/candidates/hongkou-russian-consulate --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/hongkou-russian-consulate/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/hongkou-russian-consulate --out /tmp/russian-geometry.json --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

Blender保存后实际重开，建筑几何哈希与面数一致，预览地面和摄影棚不计入建筑。作者构件各自闭合正体积，相接部分未作全楼布尔并集。墙段两端缩接至四个闭合角柱，去除墙角重叠端面；最终压缩解码后仍检查绕序。局部导出器按作者构件保留顶点，没有修改其他建筑的通用帮助文件。

网页复验：`python -m http.server 8782 --directory projects/shanghai`，另运行`node projects/shanghai/data/audit/russian-consulate-v1/qa-browser.cjs`（Playwright与Chromium，默认输出`/workspace/russian-browser*`，可用`MODEL_URL`指定地址）。场景只支持矩形外包之外的平地外围漫游，不支持室内、阳台、塔顶和坡屋面行走。40处城市原址入口不变；本件不等于四立面精确复原或全市逐栋完成。
