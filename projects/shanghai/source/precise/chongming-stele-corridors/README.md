# 崇明学宫碑廊：两长边分段候选

[独立预览](../../../stele-corridors.html) · [资产清单](../../../assets/models/candidates/chongming-stele-corridors/manifest.json) · [检查记录](../../../data/audit/stele-corridors-v1/README.md)

本件只交付两条独立30.5米长边组件，基座各宽2.5米，合计表现61米。**原文总长76.7米和南北合计15.7米预算继续保留；南北具体短段、转角、入口及完整院落布局尚待核实，没有均分或制作虚构短段。**两组件并排同向、中心间距7米仅供展示，不代表院宽、实际方位或原址配准。两侧复用共性结构假设，不证明实物细节一致或照片分别属于东西哪一侧。

## 文献、照片和分段解释

[旧馆碑廊条目](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_3.htm)记“碑廊全长     76.7米，其中，东西两侧宽皆为2.5米，长30.5米；南北长15.7米，宽2.5米，面积为191.75平方米。”精确空格和短引、响应哈希见[source-register.json](source-register.json)。2001修复是本条记录；2021文章中2001年4月至2002年6月涉及明伦堂、仪门、碑廊的工程阶段另列，不替代单体修复记录。

2×30.5+15.7=76.7、76.7×2.5=191.75支持东西各30.5米、南北合计15.7米的解释。若南北各15.7，总长92.4、面积231与原总量不符；各7.85仅为算术均分，文字未证明等长、完整分段数或转角重叠。文献没有给出本件高度、柱数、柱距和量测端点。

[2023图文](https://www.sohu.com/a/669412809_121124600)的廊下近景与[2021图文](https://m.thepaper.cn/newsDetail_forward_11469862)的碑廊图支持院侧红褐圆柱、浅色鼓形石础、靠白墙半露柱、横梁纵枋、重复弧椽/瓦底、碑墙及石铺走道的可见类型。两图侧别、拍摄年月和完整屋面未知，碑文排布也不同；不能镜像后称两侧均照片验收。原图不再分发、不取样贴图。旧藏53通是收藏总量，模型40块空白碑面不对其做数量或位置配对，未复原书法与铭文。红毯、灯笼、人物和院树未作为固定建筑建模。

## 参数和实际几何

| 参数 | 本候选 | 说明 |
|---|---:|---|
| 每条基座 | 30.5×2.5×0.15米 | 文献长宽采用基座外线解释；端点未实测 |
| 每条柱位 | 11组，柱距3.0米 | 两端各0.25米余量；10分区是估计 |
| 院侧／墙侧柱半径 | 0.10／0.085米 | 截面和半露程度估计 |
| 檐高／最高点 | 3.50／4.60米 | 屋面外形、弧率、脊帽和隐蔽背面均估计 |
| 空白碑面 | 每条20块，共40块 | 数量、位置、大小估计，非旧藏53通布局 |
| 展示中心 | 局部Y−3.5和＋3.5米 | 同向平行，7米只是展示间距 |
| 两组件展示外包 | 31.1000004×10.0899999×4.5999999米 | 从GLB计算宽深高，含檐瓦与任意展示排布 |

上层横枋缩至深1.30米以完整留在弧坡屋面下，避免原首轮横枋端头穿过灰瓦；主横梁深2.32米不变。最终几何有针对性断言，原生全景已无瓦面露木。每条长边同一个节点可独立放置；Blender保存并重开后是两份独立mesh数据，可分别编辑，不只是共享数据的对象实例。GLB面数按场景中两组件实际放置累计，而非仅按唯一几何缓冲计数。

廊内几何检查包括两组件24条纵向射线（1.1米宽核心、标高0.25/1/1.7/2.8米）与20条跨廊射线，纵向无遮挡、跨廊从开敞院侧首先到达碑墙。另有柱体与横梁控制命中。石础保守净宽1.615米，地面顶0.175米、横梁底3.32米；数值是本模型，不是实物通行标准或测量。近景圆柱采用20边、远景10边，控制命中按各自真实多边截面计算。网页漫游仍仅在整个展示外包之外，不提供廊内通行。

## 文件和复跑

使用十进制 MB；所有单文件小于100 MB。Blender面数只计建筑组件。

| 文件 | 大小 | 两组件三角面 | SHA256 |
|---|---:|---:|---|
| chongming-stele-corridors-raw.glb | 9.442068 MB | 232696 | `a2ba2371f6f01a9dc820b964669e5e51aefec9539f3d38a4a5d5c49b51522fb6` |
| chongming-stele-corridors-web.glb | 3.454884 MB | 232696 | `32eb735aa863901a57180b76a7510d85d411d77e1208a653c37d694b94c97ded` |
| chongming-stele-corridors-lod.glb | 0.643496 MB | 42200 | `b221b24f7a60a11d81303f53c8abe7e0fec65e6ea3cbde3f2fb679182c7cf7db` |
| chongming-stele-corridors.blend | 8.591937 MB | 232696 | `d6e977695d4f69461579f81fae00e5805a8e45e5ea5d482fcba8610709923be4` |

近景232,696面、1,410作者构件；远景42,200面、850构件。每作者构件封闭、正体积、绕序一致；相接或相交未作全体布尔并集。最终压缩解码后身份、面数、外包、有限顶点、零退化和24纵向射线均通过。两档保持40空碑面和11组柱位，只简化圆截面、弧线细分及瓦/椽密度。

从仓库根目录运行，依赖Blender 4.3.2、gltfpack 1.3.0和锁定Python包：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-stele-corridors/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-stele-corridors/source/build_model.py --out /tmp/stele-corridors
python projects/shanghai/source/precise/chongming-stele-corridors/source/build_model.py --out /tmp/stele-corridors --lod
python projects/shanghai/source/precise/chongming-stele-corridors/source/verify_geometry.py --assets /tmp/stele-corridors --out projects/shanghai/data/audit/stele-corridors-v1/geometry.json
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-stele-corridors/source/build_native.py -- --raw /tmp/stele-corridors/chongming-stele-corridors-raw.glb --out /tmp/stele-corridors/chongming-stele-corridors.blend --previews /tmp/stele-corridors-previews
python projects/shanghai/source/precise/chongming-stele-corridors/source/package_assets.py --raw /tmp/stele-corridors/chongming-stele-corridors-raw.glb --lod /tmp/stele-corridors/chongming-stele-corridors-lod.glb --native /tmp/stele-corridors/chongming-stele-corridors.blend --out projects/shanghai/assets/models/candidates/chongming-stele-corridors --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

复核后把原生4图、native.json和两档features同步到本件audit。网页检查需Playwright与Chromium：用`python -m http.server 8782 --directory projects/shanghai`提供页面，再运行`node projects/shanghai/data/audit/stele-corridors-v1/qa-browser.cjs`；输出`/tmp/stele-corridors-browser.json`及`.png`复核后同步audit。Node须能解析Playwright模块。

```sh
python projects/shanghai/source/precise/chongming-stele-corridors/source/verify_packaged.py --assets projects/shanghai/assets/models/candidates/chongming-stele-corridors --audit projects/shanghai/data/audit/stele-corridors-v1 --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

通用构件、原生、打包和网页流程来源见`source/HELPER_PROVENANCE.json`，不据代码复用断言实物相似。原创代码与几何MIT；原照片保留权利。本件不是全院闭环复原，南北短段与碑文仍是TODO，未替换城市源要素或完成原址配准。
