# 老永安公司主楼与屋顶塔楼外观候选

[查看模型](../../../old-wing-on-company.html) · [四件资产与摘要](../../../assets/models/candidates/huangpu-old-wing-on-company/manifest.json) · [检查记录](../../../data/audit/old-wing-on-company-v1/README.md)

本件表现南京东路635号的老永安公司外观。东北圆弧入口与南京路北立面中西段的屋顶塔楼分别建模，塔楼不在圆弧入口正上方。南京东路627号的新永安大楼、跨街天桥、先施公司及其他邻楼不在本件范围内。大东旅社、舞厅等历史用途不自动拆成独立楼栋。

## 来源与尺度

[来源登记](source-register.json)汇总实际读取的文献、实际查看的照片及冻结地图边界。[官方建筑志复核](../../../data/audit/old-wing-on-company-v1/documentary-review.json)记老楼6层、局部7层，占地5681.5平方米，建筑面积30992.3平方米；没有给出本楼准确的长宽或塔顶高度。志书塔名写“倚云阁”，市国资委及复旦／市委党史资料写“绮云阁”，保留写法差异；它不是先施公司的摩星塔。该章关于新永安的727号门牌与名录627号存在差异，不能用来改变本件635号的身份。

[地图审查](../../../data/audit/old-wing-on-company-v1/footprint-review.json)核对老永安和新永安为两个独立源对象，最近间距约10.03米。老楼粗外包约66.67×94.64米，无楼层、高度、内院或分栋部件资料；它不等于历史实测墙线，不能把地图面积与文献占地强行调成相同数值。另一份官方转刊称平面“略呈正方形”，与上述粗长方形覆盖范围尚未统一。

模型主体采用66×94米，东北圆弧半径12.4米，主屋面30米，东南局部第七层屋面34.4米；北侧塔基之后为两层开放亭，帽顶45.8米，简化天线顶54米。**以上数值、楼层标高、局部第七层范围、塔位坐标和构件尺寸均为作者设计估计。** 天线参照现代照片，不断言它是1918年原始构件，也不把杆顶当作已核实的历史建筑总高。装饰后的实际模型外包见清单及几何报告。

## 照片与简化

[照片复核](../../../data/audit/old-wing-on-company-v1/photo-review.json)记录2011年塔部近景、2013年全景以及2025年白天和夜间街面。保留可辨认的东北弧角、二楼及六楼连续铁栏长廊、逐层弧角阳台、圆气窗带、交替窗楣、北立面塔和两层开放亭。底层采用橱窗与门厅，不将先施公司的骑楼形态移用到本楼。

夜景灯光不能证明真实表面颜色。窗网、雕饰、栏杆与柱式采用简化几何，文献中的门窗数量未逐项复原；广告、招牌、室内、屋顶花园布置和跨街天桥未复原。背面、屋面及隐蔽平面为估计补全，封闭屋面不证明实楼没有内院。多期照片共同参照不等于1918年原貌或2026年测绘现状，尚未完成全部立面的照片精度验收或原址配准。

照片只供观察，不取样、不嵌入、不随包分发，各自许可见登记。公开包中的原创建模代码与几何采用MIT；文献仅保存事实摘要与出处，不推定其全文再发布许可。

## 重建与检查

从仓库根目录执行；Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender和gltfpack。

```bash
python projects/shanghai/source/precise/huangpu-old-wing-on-company/source/build_model.py --out /tmp/wing-build
python projects/shanghai/source/precise/huangpu-old-wing-on-company/source/build_model.py --out /tmp/wing-build --lod
python projects/shanghai/source/precise/huangpu-old-wing-on-company/source/verify_geometry.py --assets /tmp/wing-build --out /tmp/wing-geometry.json
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-old-wing-on-company/source/build_native.py -- --raw /tmp/wing-build/huangpu-old-wing-on-company-raw.glb --out /tmp/wing-build/huangpu-old-wing-on-company.blend --previews /tmp/wing-previews
python projects/shanghai/source/precise/huangpu-old-wing-on-company/source/package_assets.py --raw /tmp/wing-build/huangpu-old-wing-on-company-raw.glb --lod /tmp/wing-build/huangpu-old-wing-on-company-lod.glb --native /tmp/wing-build/huangpu-old-wing-on-company.blend --out projects/shanghai/assets/models/candidates/huangpu-old-wing-on-company --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/huangpu-old-wing-on-company/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/huangpu-old-wing-on-company --out /tmp/wing-packaged.json --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack --blender /usr/bin/blender
```

作者构件分别闭合，未作全楼布尔并集，不宣称整栋是单一流形。原生文件包含一个可编辑建筑网格及另计的摄影棚地面、灯光和相机，参数化源码另附。近远景的窗框、栏杆和曲面分段程度不同；压缩解码检查逐材质有向三角面及重复次数，不把面数一致当作表面等价。

网页检查需Playwright与Chromium。启动`python -m http.server 8782 --directory projects/shanghai`，运行`node projects/shanghai/data/audit/old-wing-on-company-v1/qa-browser.cjs`；可用`MODEL_URL`和`QA_OUTPUT_DIR`指定页面及报告目录。只支持整栋外包以外的地面漫游；门厅和塔亭开口不表示支持室内、登楼或穿过模型。独立展示尚未替换城市地图对象，40处城市入口另计。
