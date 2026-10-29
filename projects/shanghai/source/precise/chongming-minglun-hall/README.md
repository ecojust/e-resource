# 崇明学宫明伦堂：文字尺寸参照候选

[独立预览](../../../minglun-hall.html) · [资产清单](../../../assets/models/candidates/chongming-minglun-hall/manifest.json) · [检查记录](../../../data/audit/minglun-hall-v1/README.md)

依据旧馆20.6×12.7×10.37米文字制作独立候选，参考题注“明伦堂”的树遮庭院照片表达木立面、浅墙、灰瓦片段和抬高入口概念。**2021年官方另记高10.5米，保留为未解决的另一版本；没有平均两个高度。历史“原共有五楹”不证明现代柱网，模型五分区、门窗、前廊和屋顶均有估计。**

## 来源和尺寸解释

[旧馆明伦堂条目](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_3.htm)原句为“2001年崇明县人民政府投资修复，面阔20.6米，进深 12.7米，高10.37米，建筑面积为261.6平方米。”原文空格保留在[source-register.json](source-register.json)。1624年始建是历史记载，历史五楹／深三丈余不转成现代开间或米制柱网。

[2021年区政府文章](https://www.shcm.gov.cn/zjcm/006008/20210423/8c183cc2-f5a9-4d52-b152-9d72ec7eb5a7.html)记“现面宽20.6米，进深12.7米，高10.5米。”两个高度的量测端点和基准均未明，不判定孰为实测。2021图文记述2001年4月至2002年6月工程同时涉及明伦堂、仪门和碑廊，单体2001修复记录另列。

[题注照片所在文章](https://m.thepaper.cn/newsDetail_forward_11469862)发表于2021-02-27，照片677×451，拍摄日期未知。树木遮住主体外侧和大部分屋面；只能核部分色块、入口高差和庭院关系，不能数完整门窗、柱网、台阶或确定屋顶类型。中央浅色竖区不能分辨为门扇、玻璃或展板。没有使用未题注的崇賢館照片，也没有将大成殿的歇山／五开间描述转用到本件。照片只作观察参考，不公开原图或取样贴图。

| 参数 | 本候选取值 | 说明 |
|---|---:|---|
| 局部基座 | 20.6×12.7×0.72米 | 文献长宽解释为基座；厚度估计 |
| 墙外线 | 20.0×11.5米 | 墙、柱、基座及檐口测量端点未明 |
| 屋面宽／深 | 21.5×14.0米 | 简单双坡的设计值，未确认真实屋型 |
| 总高 | 10.37米 | 采用旧馆数值，含素脊帽；10.5米另存未解决版本 |
| 立面分区／前柱／格窗 | 5／6／4 | 都是现代形态估计，不称照片确认的柱网 |
| 台阶 | 4级 | 单闭合阶梯截面棱柱，级数与踏步估计 |
| 实际全部外包 | 21.6499996×15.2205529×10.3699999米 | 从GLB计算宽深高，含瓦端、脊帽和前阶 |

20.6×12.7=261.62平方米仅为乘积，与文献261.6平方米分开。近似相符不证明真实墙线或方向。局部正面为-Y，未作方位测量。前廊很浅，深度、圆柱截面、前梁与简栏均为原创估计；侧后墙、屋顶端部、瓦垄和色材也未照片验收。闭合中门与四格窗不是对照片中央浅色区域的事实认定。

## 资产与复验

下表使用十进制 MB；Blender面数仅计建筑本体，全部单文件小于100 MB。

| 文件 | 大小 | 三角面 | SHA256 |
|---|---:|---:|---|
| chongming-minglun-hall-raw.glb | 3.849468 MB | 52884 | `52b6c5ff980bab535b92f785bd101ba065efefa016ba21960fe3cf67bdfcbf4d` |
| chongming-minglun-hall-web.glb | 1.292168 MB | 52884 | `bf3c12e5358dc1b6b97c0add6c589ef88b6398e2c4050a29e9ec5368715b6148` |
| chongming-minglun-hall-lod.glb | 0.167132 MB | 7748 | `e86e1ed7e63d9b31035dba958ac5852d2ecd96603e9fc6ad619b35679d058fc6` |
| chongming-minglun-hall.blend | 1.791012 MB | 52884 | `97df7e8b2ae1781e4527253289232fbc9b34b8ed76c12bf8544f387a7ef5d1aa` |

近景52,884面、1,815作者构件；远景7,748面、259构件。各作者构件闭合、正体积、绕序一致；相接或相交未作单一布尔并集。四处格洞各一射线到达凹入背衬，中央闭门射线命中实体。两档保持外包，压缩解码后零退化面、身份和面数一致。

从仓库根目录运行，依赖Blender 4.3.2、gltfpack 1.3.0及锁定Python包：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-minglun-hall/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-minglun-hall/source/build_model.py --out /tmp/minglun-hall
python projects/shanghai/source/precise/chongming-minglun-hall/source/build_model.py --out /tmp/minglun-hall --lod
python projects/shanghai/source/precise/chongming-minglun-hall/source/verify_geometry.py --assets /tmp/minglun-hall --out projects/shanghai/data/audit/minglun-hall-v1/geometry.json
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-minglun-hall/source/build_native.py -- --raw /tmp/minglun-hall/chongming-minglun-hall-raw.glb --out /tmp/minglun-hall/chongming-minglun-hall.blend --previews /tmp/minglun-hall-previews
python projects/shanghai/source/precise/chongming-minglun-hall/source/package_assets.py --raw /tmp/minglun-hall/chongming-minglun-hall-raw.glb --lod /tmp/minglun-hall/chongming-minglun-hall-lod.glb --native /tmp/minglun-hall/chongming-minglun-hall.blend --out projects/shanghai/assets/models/candidates/chongming-minglun-hall --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

原生三图与重开记录输出到`/tmp/minglun-hall-previews`，复核后同步本件audit。网页检查依赖Playwright与系统Chromium：先用`python -m http.server 8781 --directory projects/shanghai`提供页面，在另一个终端运行`node projects/shanghai/data/audit/minglun-hall-v1/qa-browser.cjs`；输出`/tmp/minglun-hall-browser.json`和`.png`复核后同步audit。Playwright模块须在Node搜索路径中。

```sh
python projects/shanghai/source/precise/chongming-minglun-hall/source/verify_packaged.py --assets projects/shanghai/assets/models/candidates/chongming-minglun-hall --audit projects/shanghai/data/audit/minglun-hall-v1 --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

通用构件、门窗、屋面、原生与打包流程改编来源见`source/HELPER_PROVENANCE.json`；代码复用不证明建筑外观一致。原创代码与几何MIT；照片保留其权利。候选不含相邻碑廊、树木和实测庭院地形，只供全外包以外的平地漫游，无室内、上廊、登阶或城市原址配准。
