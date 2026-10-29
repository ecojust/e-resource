# V22：徐家汇藏书楼南楼与孙中山故居主楼室外漫游

两个模型沿用各自公开照片参照的估计外观，补齐原址定位、精确源对象替换、保守障碍与第三人称入口。南楼北侧独立藏书楼、孙中山故居旁的纪念馆均保留。没有城市运行时代码变更。

`tools/partition_baseline.py` 从实际解码的原近景 GLB 分组，保留原顶点、法线、材质、索引绕序和实例变换，不重新生成邻楼。南楼分块有7个源对象，孙中山故居分块有14个；只隐藏目标对象的组。孙中山故居共边处用冻结引擎的参考实例/三角形消除归属歧义，允许的匹配容差只用于识别归属，绝不移动原数据；每个源对象的面数另与参考核对。

`verify_partition.mjs` 使用生产 Three/GLTFLoader/Meshopt 比较原分块与分组分块的完整三角面位置、法线、材质及绕序，必须完全一致；删除邻楼的负例必须失败。早期重新生成分块的方案未通过原几何一致性检查，未安装。

`prepare_walk.py` 从真实浏览器地图要素冻结精确 Overture UUID 和 OSM 多面要素中的目标组件。碰撞只在 SHA 验证的实际模型可见时启用；失败时恢复原源碰撞。障碍来自模型底部三角面，孙中山故居采用保守凸包，排除外廊、台阶和室内行走。路径按起点、前5米、相机与相机臂检查9个宏块；仍为虚拟平地，非实测高程或实际开放通行承诺。

每栋目录保存实际地图采样（gzip）；孙中山故居还保存用于归属消歧的生成参考。`tools/generate_sun_owner_reference.py` 可重建这两个参考文件。原冻结特征表、READY及近景文件均来自版本库。

示例（项目根目录 `projects/shanghai`）：

```bash
python source/city/precise-overrides-v22/tools/partition_baseline.py --project . --decoded /tmp/baseline-decoded.glb --out /tmp/partition --id xuhui-zikawei-south-building
node source/city/precise-overrides-v22/tools/verify_partition.mjs . /tmp/baseline.glb /tmp/partition/partitioned.glb /tmp/geometry-proof.json 1595
```

先将原近景 `.glb.gz` 解压，再使用 `source/precise/xuhui-zikawei-south-building/source/decode_meshopt.mjs` 解码。孙中山故居使用 `--id huangpu-sun-yatsen-residence`，并传入解压后的 `--instance-reference`、`--triangle-reference`，验证局部编号为3433。模型、源表、归属参考与脚本 SHA 统一记录在各栋接入核验目录。

`register_walk_models.py` 仅在实际最终行走报告及原几何保持证明通过后更新登记。已安装近/远景 GLB 增补原作者许可元数据；其压缩二进制块逐字节不变，见 `installed-assets.json`。原始模型/Blender及独立预览保留。

来源：© OpenStreetMap contributors / Overture Maps，ODbL-1.0；原创模型、材质和新增工具 MIT；照片按各自 CC BY-SA 许可署名。分组验证代码适配自项目 V12 `verify_override_geometry.mjs`，不改变其原始文件。
