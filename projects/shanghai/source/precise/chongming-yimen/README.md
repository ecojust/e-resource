# 崇明学宫仪门：照片形态参照候选

[独立预览](../../../yimen.html) · [资产清单](../../../assets/models/candidates/chongming-yimen/manifest.json) · [检查记录](../../../data/audit/yimen-v1/README.md)

依据题注明确的正面照片制作曲线白端墙、弧坡灰瓦屋面、两根内柱、两侧各6个格窗分区、帘两侧各2个可见格窗分区及中央米色折帘。竖匾只保留蓝绿色底与边框，文字留空。**模型最高点7.0米是形态设计估计，文献高度9.07米另列，二者尚未调和；没有像素换算或照片比例验收。**

## 文献、照片与尺寸

[旧馆第2节“仪门”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_3.htm)记载仪门在棂星门东、儒学署大门北，2001年修复，面阔10.6米、进深9.7米、高9.07米、建筑面积102.8平方米。尺寸端点和高度基准未说明。10.6×9.7=102.82仅为算术值，不能由面积倒推墙线或柱线。2021文章的2001年4月至2002年6月工程涉及仪门、明伦堂和碑廊，不把整段工程起止改成该单体唯一修复年份。

[2023年文章中的仪门正面照片](https://www.sohu.com/a/669412809_121124600)拍摄时间未知，参考图1920×1280。其可见构件核对见[逐项观察](../../../data/model-todo/chongming-yimen-visible-features.json)与[source-register.json](source-register.json)。不把同篇航拍照片作者自动赋给本图，不再分发照片或取样作为贴图。

| 参数 | 模型值 | 范围说明 |
|---|---:|---|
| 局部基座 | 10.6×9.7×0.22米 | 长宽是文献端点的解释，高度估计 |
| 端墙外宽／下段深 | 10.24／9.3米 | 独立设计值，局部正面为-Y，未配准方位 |
| 前坡脊面／檐面 | 6.45／4.70米 | 曲率与标高估计，后坡镜像未经照片证实 |
| 模型最高点 | 7.0米 | 端墙压顶，非文献9.07米的实现 |
| 格窗竖向范围 | 1.20–3.55米 | 16个可见大分区；细格数量与框料截面估计 |
| 中央帘 | 宽1.18米，标高0.40–3.75米 | 折数、深度和尺寸估计，闭合薄实体 |
| 两内柱中心 | 局部X±1.95米 | 位置与圆截面估计，不称完整柱网 |
| 全部资产实际外包 | 10.6000004×10.7449999×7.0米 | 从GLB计算，宽、深、高；包括两级估计前阶与瓦端 |

文献三维尺寸与照片可见形态无法凭现有资料完整调和，模型优先表达可见构件关系，未将整立面强行拉伸以满足9.07米。7.0米是明确的建模选择，不代表量测结果或已纠正文献。三片视觉区域不能直接称文献三楹；窗分区也不等同可开闭门窗扇数量。

细格、瓦垄数量、接头、檐下椽端、配色与简化脊部纹样均原创估计。两级短阶作为一个闭合阶梯截面棱柱，级数仍待核。门帘后门扇、完整梁架柱网、侧后细节、精确匾联书法和雕刻均未复原。白端墙后半及后屋面镜像、后面素墙是显式假设。

## 文件与复验

模型文件使用十进制 MB；全部单文件小于100 MB。

| 文件 | 大小 | 三角面 | SHA256 |
|---|---:|---:|---|
| chongming-yimen-raw.glb | 3.899412 MB | 57896 | `bfb4b924ad76202eece00f8d33368c6c14d7352108a3aff04d40bc900ebe0521` |
| chongming-yimen-web.glb | 1.305336 MB | 57896 | `de9cdf2f2f41f92b97aaf3d851e2fb9cfb1fe52c27a57be16f8a08abbd88220a` |
| chongming-yimen-lod.glb | 0.297392 MB | 13768 | `2fe4176c7f62d5a260b2e9fbe3c191c20951ee43aadcece9e7bedd00171cc2b7` |
| chongming-yimen.blend | 1.895717 MB | 57896 | `4d4c268d4d89997c0aca031aa76d560172a66a06db90aa6de09a6af695402053` |

四个模型文件、近远景原始几何、Blender重开和压缩GLB解码检查通过。每个作者构件为闭合正体积实体；构件允许相接或相交，未声称全部模型已做布尔并集。16处格洞各一条射线均到达凹入背衬，中央射线命中幕布，未虚构帘后门扇。

仓库根目录构建；依赖为Blender 4.3.2、gltfpack 1.3.0及锁定Python版本包：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-yimen/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-yimen/source/build_model.py --out /tmp/yimen
python projects/shanghai/source/precise/chongming-yimen/source/build_model.py --out /tmp/yimen --lod
python projects/shanghai/source/precise/chongming-yimen/source/verify_geometry.py --assets /tmp/yimen --out projects/shanghai/data/audit/yimen-v1/geometry.json
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-yimen/source/build_native.py -- --raw /tmp/yimen/chongming-yimen-raw.glb --out /tmp/yimen/chongming-yimen.blend --previews /tmp/yimen-previews
python projects/shanghai/source/precise/chongming-yimen/source/package_assets.py --raw /tmp/yimen/chongming-yimen-raw.glb --lod /tmp/yimen/chongming-yimen-lod.glb --native /tmp/yimen/chongming-yimen.blend --out projects/shanghai/assets/models/candidates/chongming-yimen --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

原生检查输出到`/tmp/yimen-previews`，复核后同步本件audit目录。网页检查要求已安装Playwright与系统Chromium：先用`python -m http.server 8780 --directory projects/shanghai`提供页面，在另一终端运行`node projects/shanghai/data/audit/yimen-v1/qa-browser.cjs`；输出位于`/tmp/yimen-browser.json`和`/tmp/yimen-browser.png`。检查通过后将这两文件分别同步为audit中的`browser.json`和`browser.png`。

最终解码核验：

```sh
python projects/shanghai/source/precise/chongming-yimen/source/verify_packaged.py --assets projects/shanghai/assets/models/candidates/chongming-yimen --audit projects/shanghai/data/audit/yimen-v1 --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

通用构件和原生／打包流程的来源见`source/HELPER_PROVENANCE.json`。本件独立制作曲线轮廓和格窗帘幕，复用代码不证明仪门与其他建筑相同。原创代码与几何MIT；原照片保留其权利。本件不含院落植物、邻楼、实测铺装或室内；独立漫游只绕模型外围，不穿帘或攀爬，未替换城市源要素或增加原址配准完成数量。
