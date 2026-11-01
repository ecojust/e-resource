# 旧上海市博物馆江湾馆舍：原创外观源码

本包以现存地图主源 1860 的完整轮廓和与其重叠的门楼源 1931 为落位基础。西向中央门楼、两层南北翼按现代照片作外观建模；东中后厅仅为简化估计低体量，其现有年代、范围与细节未获后侧照片核实。510、1262 两院内独立源及医院邻楼不并入。全局接入由城市目录另行执行，本资产本身不删除其他建筑。

中央西面保留单圆拱、两八角窗、五条高竖窗、六柱五开间敞廊与退进窗墙，黄瓦双檐包含封闭屋盖、阁层回墙和山墙。翼部为照片可见的现状两层，不等同历史单层。1935 名录、1936 完成、1937 开馆分别保留出处含义。二手条目 24 米与 10.5 米只作名义参考，未测绘、未核原设计标高；中央石身 12 米、翼墙 10.5 米及所有装饰/窗距均为作者估计。背面窗数、柱廊背侧、瓦垄、卷纹与内部支承为简化推定，不声称逐件复原。

公开包不含第三方照片或贴图。作者实际查看的三张现代外观图及其哈希在 `author-reference-inspection.json`；团队更广的文献与看图记录在 `source-register.json`、`documentary-review.json`、`photo-review.json`，不能把团队阅读数说成作者个人看图数。几何 MIT，地图来源 ODbL-1.0，照片仍由各原来源持权。

## 生成

使用 Python 3.11+，依赖版本见 `source/requirements.txt`。在此包根目录执行：

```sh
python source/build_model.py --out build
python source/build_model.py --lod --out build
python source/verify_author.py --out build/author-geometry-checks.json
python source/verify_author.py --lod --out build/author-geometry-checks-lod.json
python source/verify_serialized.py --asset build/yangpu-former-shanghai-city-museum-raw.glb --probes build/surface-probes.json --out build/author-raw-rays.json
python source/verify_serialized.py --asset build/yangpu-former-shanghai-city-museum-lod.glb --probes build/surface-probes-lod.json --out build/author-uncompressed-lod-rays.json
blender -b -t 2 --python source/build_native.py -- --raw build/yangpu-former-shanghai-city-museum-raw.glb --out build/yangpu-former-shanghai-city-museum.blend --previews build/native --samples 12 --views gallery,front,oblique,rear,roof,entrance,roofdetail,wing
python source/package_assets.py --raw build/yangpu-former-shanghai-city-museum-raw.glb --lod build/yangpu-former-shanghai-city-museum-lod.glb --native build/yangpu-former-shanghai-city-museum.blend --out assets --gltfpack /path/to/gltfpack
```

验证使用 Blender 4.3.2、gltfpack 0.25。`package_assets.py` 使用 `-cc -noq -vnf -km -kn -ke`，保持位置 FLOAT32。Web/LOD 应各自解码后与对应未压缩版本逐材质、保绕序的 FLOAT32 三角集合一致。LOD 保留所有开口与封闭体，仅降低瓦垄/栏杆等离散度。原生文件中名为 “Preview only — not part of building” 的摄影台、灯与相机不是建筑；保存后实际重开核对建筑网格哈希。

## 几何边界与修订

所有墙洞用面域差集留实际洞口，窗玻璃位于墙内，拱门后挡界定未知室内；不提供入馆或楼上漫游。接触 510/1262 的主源内墙保持不动，只在接触跨度去掉新装饰外挑、估计窗及屋面唇，不用院地板填补。中央连续石台从 10.08 米到 12 米，与 10.02–10.12 米屋面交叠 4 厘米；同位西前墙终止于 10.08 米，避免重叠外表面。庭院没有地板，入口仅 9 厘米浅门槛。

初版 v1 有中央返回墙共面重叠；v2 改为单体后误留 0.38 米水平空隙，均未作为最终资产。v3 同时修复连续支承与邻源接触装饰，并增加 10.15/10.25/10.45 米回归射线；每次失败和验证保留于作者修订记录。屋顶真实水平出挑与地面行走碰撞范围须由城市映射审查分别处理。

`source/HELPER_PROVENANCE.json` 记录复用的 MIT 通用几何/屋面和流程代码的原提交、原 blob 与原 SHA256；新馆平面、立面和尺度独立编写，没有复制另一栋楼的成形网格。最终复制到独立目录实际重建，原始/LOD GLB 和结构记录逐字节比对。未核后厅细部及两凹院小源继续在待办保留。
