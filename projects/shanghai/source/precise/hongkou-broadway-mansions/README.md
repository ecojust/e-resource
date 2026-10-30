# 上海大厦／百老汇大厦历史主楼：外观候选

[独立查看与外围漫游](../../../broadway-mansions.html) · [模型清单](../../../assets/models/candidates/hongkou-broadway-mansions/manifest.json) · [检查记录](../../../data/audit/broadway-mansions-v1/README.md)

本件参照Livelikerw的2014年1月照片和《上海名建筑志》文字制作历史主楼外观候选。表现内凹四翼体量、褐色砖饰面、成组上部退台、矩形窗洞与分格窗框、竖向砖肋、楼板、屋顶平台与女儿墙。照片右侧浅色邻楼没有纳入，未伪造酒店字牌和不可辨文字。原图仅本地研究，没有照片贴图或第三方图像再分发。

## 依据和解释

地方志记高76.7米、22层、11层起收进；百科另记77米、地上21层，地图19层。三种层数没有调和。候选采用76.7米为最高点、22个设计分层，**不证明22层均与真实窗层对应**。前两层分别4.8和3.8米，其后多数3.32米，顶部补齐到75.7米再加1米女儿墙，全部层高为估计。

平面直接取已冻结复核中`582fd5f8-2a90-3eba-9fce-81b358492d0b`的局部米制内凹地图部件；没有拿两个同源大厦UUID重复建楼。地图部件层级和历史墙线未确认，宽深只作地图参照，不能视为实测历史尺寸。自第11设计层用成组局部X截取边界33、29、23、18及12米表现逐级退台；这些退距、顶层范围及左右对称都为设计估计，不是照片标定或实测屋顶。

窗口数、等距窗网、窗框、窗台、背面、四翼隐蔽立面、顶面与入口雨篷均含估计。咖啡色和浅色基座参照照片观感，采用纯色粗糙度材质，尚无真实砖缝、表面风化或现场PBR扫描。历史暗红花岗石底层文字不直接冒充2014年所有基座饰面。6600平方米用地与24596平方米建筑面积未用于反推楼体边长；门牌2／20号冲突仍保留。

[逐项资料、许可与照片观察](source-register.json) · [设计分层与窗数](design-input.json) · [地图来源复核](../../../data/model-todo/heritage-next-footprint-review.json)。原图署名Livelikerw，CC BY-SA 3.0（https://creativecommons.org/licenses/by-sa/3.0/）；模型不嵌入该照片。原创代码和几何采用MIT；地图派生轮廓© OpenStreetMap contributors，ODbL-1.0，不改变其许可。无开放许可的地方志和官方图文仅短引事实及出处。

## 复跑

从仓库根目录，Python依赖见`source/requirements.txt`，Blender 4.3.2，gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/hongkou-broadway-mansions/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/hongkou-broadway-mansions/source/build_model.py --out /tmp/broadway
python projects/shanghai/source/precise/hongkou-broadway-mansions/source/build_model.py --out /tmp/broadway --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/hongkou-broadway-mansions/source/build_native.py -- --raw /tmp/broadway/hongkou-broadway-mansions-raw.glb --out /tmp/broadway/hongkou-broadway-mansions.blend --previews /tmp/broadway-previews
python projects/shanghai/source/precise/hongkou-broadway-mansions/source/package_assets.py --raw /tmp/broadway/hongkou-broadway-mansions-raw.glb --lod /tmp/broadway/hongkou-broadway-mansions-lod.glb --native /tmp/broadway/hongkou-broadway-mansions.blend --out projects/shanghai/assets/models/candidates/hongkou-broadway-mansions --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/hongkou-broadway-mansions/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/hongkou-broadway-mansions --out /tmp/broadway-geometry.json --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

近景保留窗框与竖肋，远景保留全部同位置窗洞和玻璃，简化窗框、窗台及竖肋；两档外包相同。作者构件闭合正体积，各构件未进行全楼布尔并集，不表示支持室内游览。Blender内建筑与预览地面分开，保存后实际重开检查建筑几何哈希与面数。预览用地面只是展示，无地理意义。

网页检查：`python -m http.server 8782 --directory projects/shanghai`，另运行`node projects/shanghai/data/audit/broadway-mansions-v1/qa-browser.cjs`（需Playwright和Chromium）。脚本默认输出到`/workspace/broadway-browser*`，可用`MODEL_URL`指定发布后页面地址。

独立模型外围漫游使用整个楼体矩形外包阻挡；不支持进入内凹院落、室内、登楼、楼梯或退台行走。未地理配准或替换城市源对象，不增加40处原址入口，不计为全市逐栋历史复原完成。
