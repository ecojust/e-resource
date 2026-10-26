# 上海逐栋照片参照复原 · v6首批

本目录为继续扩展全市近景的逐栋源码。首批包含日清大楼、中国通商银行旧址、交通银行旧址三栋；项目现有13栋外滩历史建筑和4栋陆家嘴地标。16区普通楼基线仍提供1,708宏块、1,796,419个建筑及部件要素、169,320近景分块。全市真实门窗和立面尚未逐栋核验，普通楼参数细化不能当作全市照片复原已完成。

## 三栋资产与重建入口

表中MB采用十进制1MB=1,000,000字节；[完整字节、SHA256与来源说明](../../../data/bund/REALISM_V6.md)另列精确值。每个文件均小于100,000,000字节。

| 建筑 | 网页GLB | 原始GLB | Blender工程 | 远景GLB | 源码与证据 |
|---|---|---|---|---|---|
| 5号 · 日清大楼 | [8.73 MB](../../../assets/models/bund/web/bund05.glb) | [14.91 MB](../../../assets/models/bund/bund05.glb) | [24.07 MB](../../../assets/native/bund/bund05.blend) | [2.07 MB](../../../assets/models/bund/lod-v4/bund05.glb) | [说明与来源](bund05/README.md) · [构建脚本](bund05/build_model.py) · [原生预览核验](bund05/native-preview-review.json) |
| 6号 · 中国通商银行旧址 | [8.44 MB](../../../assets/models/bund/web/bund06.glb) | [13.01 MB](../../../assets/models/bund/bund06.glb) | [18.72 MB](../../../assets/native/bund/bund06.blend) | [0.96 MB](../../../assets/models/bund/lod-v4/bund06.glb) | [说明与来源](bund06/README.md) · [构建脚本](bund06/build_model.py) · [原生预览核验](bund06/native-preview-review.json) |
| 14号 · 交通银行旧址 | [6.73 MB](../../../assets/models/bund/web/bund14.glb) | [9.84 MB](../../../assets/models/bund/bund14.glb) | [15.05 MB](../../../assets/native/bund/bund14.blend) | [1.44 MB](../../../assets/models/bund/lod-v4/bund14.glb) | [说明与来源](bund14/README.md) · [构建脚本](bund14/build_model.py) · [原生预览核验](bund14/native-preview-review.json) |

三栋都有真实连续开孔墙、侧壁、内退玻璃和独立框，不以整张照片平板替代建筑。5号的双山花与三面凸窗、6号的五山墙四圆尖塔与三拱入口、14号的阶梯塔冠与黑石入口均由实体构件组成。各栋绝对高度、不可见部分与精细构件尺度仍按来源标明推定。

玻璃采样范围分别为5号中央6窗112片、6号中央6窗127片、14号上层28窗137片。原JPEG只赋给逐片核对的清晰玻璃，排除照片黑框和遮挡；墙面、框、石柱、未见部分与未选窗保留几何材质。原始／网页模型嵌入各自一张原图，远景轻量模型不携带照片。反射来自固定拍摄时刻，不是完整立面多视角摄影测量。

三栋当前玻璃嵌在框前脸后约20mm的槽位，该深度为明确推定，墙洞、窗框、原图字节与逐片UV不变。HTML对明确照片玻璃采用captured-radiance材质，取消重复场景受光、投影和HDR；仍使用源 `toneMapped` 与统一色调映射，不能称为原像素直出或去光照PBR。照片石墙与普通玻璃保留原路径。正常设备局部阴影为4096×4096、48m半范围，低内存1024×1024并按硬件上限约束。

三栋楼前新增844.50㎡有界估计铺装与3块0.075m支持面，独立属于原街景道具，不混入建筑GLB；见[街景重建入口](../street/frontage-v6/README.md)。逐栋复原按[细化验收标准](../../../data/audit/precise-buildings-v6/DETAIL_STANDARD.md)记录真实依据与推定范围；07、09及222仍为未上线候选。

v6启动包尚待生成及核验；规划仍为本地保存原14栋核心地标，本批新增3栋的模型、远景变体及参考照片从固定版本按需联网加载。17栋是项目地标总数，不表示17栋模型字节全部随ZIP打包；旧v5包不代表本轮更新。

## 保留目录后重建

下载单栋源码时须同时保留相邻 `common/`、该栋冻结JSON、被引用的原照片和字体。只下载一个 `build_model.py` 不包含全部输入。完整项目仓库可按如下布局使用：

```text
source/bund/photo-rebuild-v6/
  common/
  bund05/
  bund06/
  bund14/
```

从项目根目录运行所需的一栋：

```sh
python source/bund/photo-rebuild-v6/bund05/build_model.py --output exported/bund05
python source/bund/photo-rebuild-v6/bund06/build_model.py --output exported/bund06
python source/bund/photo-rebuild-v6/bund14/build_model.py --output exported/bund14
```

构建器使用Python、NumPy、支持约束三角剖分的Shapely；05、14号字牌还需要fontTools。Pillow／SciPy用于重算部分照片控制点，生产构建读取已冻结控制JSON时不需重跑这一步。精确输入、命令和依赖以各栋README为准。共享[工具说明](common/README.md)解释原GLB、Blender工程与网页／远景压缩流程；预览地面、灯光与相机独立保存，不属于建筑资产。

几何、原图字节、逐片UV、封装和原生预览已完成核对；三栋网页技术检查通过，共15组采集记录；主审实际查看其中10张截图，接受本轮接入表现。该轮采集早于后续网络／样式补丁，新v6启动包仍待生成和核验。详见[本轮验证范围](../../../data/bund/REALISM_V6.md)。原10栋外滩模型继续使用[上级源码链](../README.md)，未被这三套构建器替代。

## 来源与许可

2025年三张主图作者均为Suicasmo，CC0-1.0；它们原字节嵌入所选玻璃。5号2011侧视参考为Can Pac Swire、CC BY-SA 2.0；6号1908书页属公版；14号各年代斜视保留各自的CC BY／CC BY-SA许可。没有许可的机构图、HTML全文和失败请求缓存不随包发布。

原创程序和独立几何采用MIT；地图轮廓与派生定位保留OpenStreetMap／Overture和ODbL-1.0署名。字体子集保留SIL OFL。所有照片和字体的具体许可见逐栋资料及common/fonts，不以代码MIT覆盖外部素材。
