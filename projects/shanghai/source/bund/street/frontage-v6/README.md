# 05／06／14楼前铺装：v6追加源码

本目录保存已安装的离线追加源码；当前生产仍为一个街景prop。只追加当前三栋主临街面的缺失铺装，不生成07/09铺装，也不处理未知巷道、楼间空地或内部院子。平面范围见 `frontage-plan.png`；它是几何审查图，不是浏览器效果图。

## 范围与证据

沿各栋冻结`front_edge`的两个端点，分别按已确认外向法线投射至**现raw模型实际道路外边界**，再沿该道路外边界构成有限包络。正向约束避免05在延安东路路口误选更近的楼侧道路。不得无条件选择最近道路、放大矩形或向路面铺满。

| 建筑 | 新增面积 | 最大包络宽度 | 当前漫游起点 |
|---|---:|---:|---|
| 05 日清 | 236.7703㎡ | 18.0649m | 新支持面内 |
| 06 中国通商 | 433.3667㎡ | 20.6749m | 新支持面内 |
| 14 交通银行 | 174.3634㎡ | 12.9853m | 原有支持面内，未重复加面 |

总新增844.5004㎡；宽度是沿继承道路模型边界的重建范围，**不是实测人行道宽度**。形体限制为已确认公共临街边正前方，宽度上限24m沿用旧frontage工具的范围约束。主代理已检查2025照片中的连续铺装，铺装材质复用现有`BundFrontagePaving`灰石；未复制照片像素或虚构花纹、台阶。

差集排除实际旧raw的铺装、路缘和排水面，旧sidecar全部支持面，实际沥青面、水体、来源洞口和草床；建筑负掩模包括旧10栋、新05/06/14及已冻结07/09、当前宏3064个普通要素。建筑外轮廓内的庭院一并保留为空，沿用旧街景0.08m建筑安全间隙。该宏/已知冻结输入是明确的范围，不声称检查了所有上海建筑。

地面下沿`.003m`、上沿`.075m`，继承西侧人行道的模型基准；不代表防汛墙、道路或楼门的实测绝对高程，不推定新楼梯。未放置树木、灯具或新家具。

## 原资产守恒与实际检查

合并工具直接读冻结原raw GLB，保留旧二进制buffer前7,435,368字节，16种原材质、16个原primitive及其所有accessor、bufferView、节点逐值不变，只追加一个新铺装primitive。原138,478个三角形全部保留；新增352个，总138,830个。

网页GLB仍使用`-cc -noq -kn -km -ke`，无位置量化。实际项目Three GLTFLoader＋MeshoptDecoder验证：旧网页三角形在新文件中零缺失；新raw与新web的全部位置Float64、材质、绕序和重数完全相等。原网页材质数值完全相同；raw到web的材质标量只存在原gltfpack已有的Float32序列化，不声称法线逐位相同。

原22个sidecar feature及3479个家具/树障碍逐值保留，只追加3个`.075m`支持面并更新raw/web SHA绑定。实际`StreetInteraction`加载新SHA后，在三处内部点返回对应支持面；owner隐藏后均返回null。没有增加第二个prop。

新增面的Float32表面边界最大舍入差约`0.0000074m`，平面面积差`0.000638㎡`，远小于旧sidecar允许的0.15mm边界精度；未转换的构造平面对排除面交叠为零（数值残差量级）。报告单列转换后的微小交叠面积，未以“严格零浮点交叠”误述。12个转换后面积严格为零的新三角形被去除，旧三角形没有删除。

证据：项目 `data/bund/validation/street-frontage-v6*.json`。在第二个全新输出目录重建，raw/web/sidecar三份SHA完全一致。路口负控测试验证较近的侧街不能取代正前方道路，无正前道路或超宽时拒绝生成。

## 重建

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
python append_frontage.py --inputs ./inputs --output /path/to/new-output \
  --ids bund05 bund06 bund14 --gltfpack /path/to/gltfpack

node verify_street_web.mjs /path/to/shanghai_project /path/to/this-stage
python test_frontage_bounds.py -v
```

所有源数据在`inputs/`由`source-manifest.json`锁定SHA，无网络、无生产写入。未来07/09应先冻结其输入与当时的街景基线，再以`--ids bund07 bund09`追加，不能把现已完成的三栋重复覆面。没有完整正前道路边界时工具会失败，不自动扩大区域。

历史首次范围试验05误选更近侧街，已废弃，**不可安装**。首次试验仅保存在开发审计目录，不属于发布源。


## 发布输入与入口

完整当前入口为项目根 `tools/build_bund_street.py --gltfpack /path/to/gltfpack`，可加 `--project /path/to/project`；`--output /fresh/output` 仅重建验证，不安装。所有冻结输入均按 `inputs/source-manifest.json` 逐字节SHA校验，路径相对本目录，无网络。`inputs/assets/models/bund/` 是有意保存的 **v5原始/压缩基线**，不是冒充v6新输出；直接追加原raw是保存旧几何逐字节不变的构建方法。当前runtime/source目录的最终raw/web均已同步。

项目原 `source/bund/street/build_street.py` 仍是完整v5程序化源，历史组合驱动保存为 `rebuild_baseline_v5.py`；该驱动必须显式 `--project` 指向隔离的旧输入项目，不可覆盖当前v6目录。新入口不需要重算/改变该历史基线。没有街景 `.blend` 文件或Blender运行依赖；rawGLB为可编辑网格。

附带 `verify_street_web.mjs` 的 STAGE 参数应指向同时有 `inputs/` 和 `output/` 的验证目录；它使用PROJECT内真实Three/Meshopt模块。将 `inputs` 链接至本目录inputs，将 `output` 指向项目入口生成的新输出即可复验。`test_frontage_bounds.py` 为三项有限道路投射负控。参考图 `frontage-plan.png` 只是几何图，未替代实际浏览器验收。

许可：原程序化代码/原创网格MIT；OpenStreetMap派生道路/建筑/源数据ODbL-1.0，© OpenStreetMap contributors。照片保留原来源许可，本追加不嵌入照片像素。冻结原GLB的copyright保持不变。
