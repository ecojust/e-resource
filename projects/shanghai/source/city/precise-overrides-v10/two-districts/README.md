# 松江方塔与真如寺正殿：原建筑替换准备

本目录只记录精确源身份分组、保留邻楼和观景候选，不是精模外观或网页验收。两栋源四边形仅用于身份与原城市替换，不能将其自动当成建筑墙线或屋檐线。精模需另据建筑资料构造。

两项新目标为松江方塔 macro14-13709-6706/local306（原同近景块15要素，保留14邻）及真如寺正殿 macro14-13716-6693/local1947（原10要素，保留9邻）。完整候选13目标、7宏、11近景块、175源要素，其中162邻要素保留。仅两新variant被生成，原9variant及原11目标完全保留，现有25导航和4个普通目录宏的字节锁未改。

新variant经实际vendored Three/Meshopt解码，位置/材质/绕序逐面Float64一致；法线不宣称逐位相同，有限浮点差异低于既有1e-7分量和1e-5度门槛。实际所有13目标的独立/全体/空owner、near退出、恢复及销毁检查通过。旧块几何报告是在源/资产SHA核验后复用，未假称重新生成；本轮runtime验证实际读取全部far及variant。

方塔观景点是南侧24m几何候选：公开OSM上下文没有步道，不称已验证道路或入口。正殿南面天王殿local41完整保留；南14m候选需要现有相机自动缩臂，源几何14/8.4/5.04m后臂受阻而3.5m后臂有限检查清晰，尚未在浏览器观察该行为。北侧映射步道的安全后视候选单列备用。禁止为构图删除天王殿，或将源足迹检查当成地面、台阶、公共通行、植被及真实模型检查。

`navigation-proposals`均为模型/网页接受前的提案；实际模型边界、默认相机及overview需另核验。几何元数据、官方名义尺寸、估计比例、来源许可和最终网页状态由各栋模型源包分别说明。

## 可复核构建

使用本目录`inputs`和项目内冻结城市数据，可在新的隔离目录运行`tools/build_precise_overrides.py --project PROJECT --output NEW --geometry-input-root INPUTS --ids`（追加13个geometry-input的目录名）及`--asset-prefix assets/city-overrides-v6 --gltfpack GLTFPACK`。再运行`node tools/verify_override_geometry.mjs NEW/geometry-comparison-input.json`和`node tools/verify_override_runtime.mjs PROJECT NEW/precise-buildings-v6.json`。只有实际验证成功才会生成complete registry。

`compose_incremental.py`用于本轮增量组合，需要原先已审核工作目录；历史报告中的工作路径是实际证据来源，不表示用户机器自动拥有这些目录。上述完整重建入口不依赖这些历史工作路径。项目代码许可沿用MIT，原始OSM/Overture数据保留ODbL及各自署名；本包不重新授权原始城市资料。
