# 全市普通建筑近景生成 · v5

本目录把现有上海建筑轮廓与高度依据转换为可按需加载的近景几何：凹窗、实体门、连续厚窗框、窗台、基座和檐边。家宅、公寓、工业、办公及未知五类使用不同构件组合。明确的来源类型优先；类型缺失时才按高度和面积选择，并保留 `family_is_inferred`。门窗位置和多数构件尺度属于参数推定，不能视为与外滩逐栋照片复原相同的现场精度。

最终构建状态：**全市模型、独立审计及浏览器场景验收已完成**。CI任务范围覆盖原有16区、1,708个宏分块中的1,796,419个普通建筑及部件渲染要素；完整产物已安装并通过独立文件、覆盖、保护几何审计和浏览器场景验收。

[CI构建记录](../../../data/audit/city-detail-v5/ci-build-summary.json)保留任务时间、源提交与终结事件对账；时间包括CI安装和上传，不是单纯几何生成耗时。

## 输入与保持项

主输入为 `data/fullcity-raw` 保存的完整Polygon/MultiPolygon、孔洞、来源属性、稳定ID和原属分块。几何坐标使用各宏分块的经纬度原点，X东、Y上、Z南，单位米。近景与其远景宏块共享原点。

渲染要素对账保持：1,796,116个原可渲染要素 −98个精细地标替换 +401个父体剩余足迹 = **1,796,419**。这包括建筑部件，不是独立楼宇数量。保留 `data/landmark-exclusions.json`、`data/parent-residual-overrides.json` 的对应关系；父体剩余部分不恢复为完整塔楼足迹。

高度继续采用原项目解析结果及依据：源height → 楼层数×3.2m → CMAB严格轮廓匹配 → CNBH栅格 → GHSL区域均高 → 标注的缺省值。新窗格不能反过来改变楼层、高度或原始足迹。先核对冻结的高度输入，再生成近远两套表示。

126处已核验屋顶沿用 `roof_geometry.py` 及原屋型、坡高、方向和来源版本，保留原屋面及上坡墙，不因近景细化改成平顶，也不加无依据的出檐。来源清单见[屋顶说明](../../../data/roofs/README.md)。全量新产物的最终屋顶核验结果为 **通过：98处地标排除、401个父体残差与126处有据屋顶；屋顶实际解码三角精确保留**。

## 完整源属性审计

除缓存的MVT属性外，还直接核查官方 Overture `2026-10-21.0` GeoParquet。以 `source_layer:UUID` 对齐行政边界内1,796,667条原始记录，全部匹配。该原始记录集合与扣除地标、处理父体残差后的渲染要素集合不同。

完整源没有补出新的height、num_floors、class、subtype、屋顶形状/尺寸/方向、外墙材质/颜色值；候选源schema未提供窗、门、入口字段，新增可用真实窗门位置为0。缺值按未知处理，不能当作“没有窗门”。126处保护屋顶的关键属性也与完整源匹配。

审计只读取所需列与候选行组，没有下载全球几何。原始 Range 缓存属于稀疏列块，不能当作完整Parquet发布。可审计投影、源索引和字段比较见[完整源属性审计](../../../data/audit/city-detail-v5/source-attributes/README.md)。

## 生成与组织

本次全量生成使用 `freeze-v6`，安装到本目录的四个源码文件是 `build_city_v5.py`、`geometry_engine.py`、`pack_client.py` 和 `gltfpack_server.mjs`。较早冻结版与pilot保留为开发历史，不作为当前全量结果。`build_city_v5.py` 为入口，`geometry_engine.py` 生成构件。五个族名称为 `house`、`apartment`、`industrial`、`office`、`unknown`；明确house类别优先于宽泛的residential提示。新入口、窗位、开间和构件尺寸保留推定状态。

结构墙对每段原足迹边生成一片连续带孔平面：窗为真正孔洞，门为底部缺口，由GEOS constrained Delaunay三角化。洞口侧壁共用规范化的世界坐标float32顶点，精确焊接保留硬法线；结构墙不再依赖各开间独立变换拼接，避免旋转与大坐标下出现浮点白缝。窗框、玻璃、窗台和门细节仍使用GPU实例。中庭檐边按内环方向闭合。

该生成器已独立通过10个覆盖五建筑族、轴向/旋转和中庭的严格几何案例，边配对检查没有T接点；126处有据屋顶的字段、屋面及上坡墙逐float32三角完全保留。[墙体边界报告](../../../data/audit/city-detail-v5/geometry/cdt-structural-boundaries.json)和[126屋顶报告](../../../data/audit/city-detail-v5/geometry/all-126-source-roofs-cdt.json)保留具体检查范围。上述是生成器验证；完整发布产物另已通过全量结构/SHA/归属检查、全部1,708个远景真实解码、87个近景分层样本真实解码及126处屋顶守恒核验，具体范围见[发布审计](../../../data/audit/city-detail-v5/release/README.md)。

远景保持1,708个宏块的组织方式并增加逐要素ID。近景先按250m归属划分，再以完整要素中位拆分，目标为每块约180,000个展开三角；不为满足预算切断单栋要素。本次完整清单记录111个单要素预算例外，保留完整要素；文件大小和运行时预算另行检查。

输出位于独立目录，发布安装目标为 `assets/city-detail/`。原 `assets/city/` 保留作原版本与回退。顶层manifest的远景记录包含 `file`、`feature_ids_file`、`feature_table_file`、`near_manifest_file`。各宏块的 `READY.json` 记录近景文件、1起始的 `featureLocalIds`、三角数、展开三角数、几何缓冲大小和包围范围；完整归属记录在 `feature-table.gz` 与 `ownership.gz`。

near文件为 `near/<id>.glb.gz`：先以Meshopt `-cc -noq -mi -kv -km -ke` 压缩GLB，保留float32位置、不做坐标量化，再以gzip等级6、`mtime=0` 确定性封装。`size_bytes`、`bytes`、`sha256`对应存储的gzip；`content_encoding:gzip`、`decoded_size_bytes`、`decoded_sha256`对应解压后的GLB。两种大小均须小于100 MB。far仍为普通Meshopt `.glb`，各顶点保留精确源要素ID；`published_files`只校验存储文件，解码元数据留在near记录中。

运行时先校验、解压，再送入GLTFLoader；完整near可显示后才隐藏其对应far要素，退出近景或加载失败时恢复原表示。运行时同时约束请求、展开三角、几何缓冲和缓存；单文件小于100MB不等于可同时加载全部近景。

## 导入Blender或其他编辑器

near的gzip封装内仍是Meshopt压缩GLB，直接解gzip不等于已转成普通编辑器格式。请保留 `assets/city-detail/macros/14-13719-6695/READY.json`，以及其记录中的 `near/-3_1-s1-s0-s0.glb.gz` 相对路径；不要根据near的逻辑ID自行改名。以下命令从项目根目录运行：

```sh
npm ci --prefix source/city/detail/tooling --ignore-scripts
python tools/unpack_model.py assets/city-detail/macros/14-13719-6695/near/-3_1-s1-s0-s0.glb.gz exported/ordinary-near.glb --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack
```

`unpack_model.py`自动寻找上级 `READY.json`，验证stored和decoded两份大小/SHA，解开gzip并转换为普通GLB；原发布文件保持不变。单独保存某个near文件时，可导出对应near记录并通过 `--metadata record.json` 显式提供它。之后在Blender的“文件 → 导入 → glTF 2.0”中选择输出文件即可，无需重新生成建筑。

[实际导入证据](../../../data/audit/city-detail-v5/blender-import.json)记录了这个9要素普通near样本：gzip为0.063 MB，解码Meshopt GLB为0.31 MB，转换后的普通GLB为0.96 MB。Blender 4.3.2实际导入4,144个网格实例，展开三角91,936，与源清单一致；坐标有限。检查范围是单一样本，不是全城模型的Blender审计。

## 重建

已生成的GLB可跨平台使用，查看或下载模型不需要重新生成。以下环境仅供复现生成结果与继续开发。

冻结参考环境为 **Linux x86_64、CPython 3.12.14、Node 24.19.0、npm 11.9.0**，压缩器为 **gltfpack 1.3.0**。依赖交付包含：

- [requirements.lock](requirements.lock)：必要Python依赖的精确版本及原始发行wheel SHA256，安装时强制二进制wheel和hash核对。
- [wheel-lock.json](wheel-lock.json)：各原始wheel的文件名、下载URL、平台标签、字节数和SHA256。
- [environment-lock.json](environment-lock.json)：冻结参考环境、生成源码与输入hash，以及GEOS 3.14.1、PROJ 9.8.1、GDAL 3.12.2等原生库版本。
- [tooling/package-lock.json](tooling/package-lock.json)：gltfpack 1.3.0的npm解析地址与完整性值；`tooling/.gitignore`排除本地`node_modules`，仓库不附带依赖安装目录。

这些平台wheel hash对应Linux x86_64与CPython 3.12。Windows、macOS、ARM或其他Python ABI须选择相应平台wheel并单独记录、验证环境，不能直接用这些hash声称得到同一平台依赖。`environment-lock.json`中的原机器路径仅作审计记录，安装时使用自己的目录。

以下命令从项目根目录执行，假定已安装上述Python、Node和npm版本。先检查版本、建立独立Python环境并安装锁定依赖；只需为重建运行一次：

```sh
python3.12 --version
node --version
npm --version
python3.12 -m venv ../shanghai-v5-venv
../shanghai-v5-venv/bin/python -m pip install --require-hashes --only-binary=:all: -r source/city/detail/requirements.lock
npm ci --prefix source/city/detail/tooling --ignore-scripts
```

`npm ci`得到的CLI为 `source/city/detail/tooling/node_modules/.bin/gltfpack`，持续压缩服务使用的WASM库入口为 `source/city/detail/tooling/node_modules/gltfpack/library.js`。将两条路径分别传给 `--gltfpack` 和 `--gltfpack-library`；后者不是CLI路径。先在项目以外的输出目录验证输入和抽样，再运行全量：

```sh
../shanghai-v5-venv/bin/python source/city/detail/build_city_v5.py --project . --output ../shanghai-v5-build --all --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack --gltfpack-library source/city/detail/tooling/node_modules/gltfpack/library.js --plan-only
../shanghai-v5-venv/bin/python source/city/detail/build_city_v5.py --project . --output ../shanghai-v5-build --macros 14-13719-6695 --workers 2 --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack --gltfpack-library source/city/detail/tooling/node_modules/gltfpack/library.js
../shanghai-v5-venv/bin/python source/city/detail/build_city_v5.py --project . --output ../shanghai-v5-build --all --workers 2 --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack --gltfpack-library source/city/detail/tooling/node_modules/gltfpack/library.js
```

复跑使用相同输出目录，逐一核对 `READY.json` 与已发布文件SHA后继续构建；冻结输入、配置和产物状态必须匹配。两个Python工作进程各调用一个持续运行的未修改gltfpack WASM服务，减少进程启动成本；若几何或配置变化，必须使用新的独立输出目录。发布只保留压缩后的near/far及重建输入、源码和清单，临时raw生成文件可删除。最终采用的源码冻结版本与完整命令：**freeze-v6；CI源提交 `764e6d94d0c5a2daacc3602852e4779cc98de139`，按冻结计划的16个分片分别以 `--macros`、`--workers 2 --target-triangles 180000 --microcell-m 250.0` 调用生成器；CLI与WASM库使用锁定的gltfpack 1.3.0。完整单机重建命令见上文**。

| 最终核验 | 记录 |
|---|---|
| CI开始 / 最后任务结束 / 用时 | 2026-10-26 03:36:47 UTC / 2026-10-26 04:12:13 UTC / 35分26秒（16分片并行CI全流程，含安装、校验与上传；不含本地检索和发布核验） |
| far宏块 / near分块 | 1,708 / 169,320 |
| 普通要素总量及16区覆盖 | 通过：16区、1,708宏块、1,796,419个唯一要素，逐要素近景归属完整 |
| near存储合计 / 最大gzip文件（MB） | 9329.01 / 0.19 |
| near最大解码GLB（MB） | 1.88 |
| far合计（MB） | 551.25 |
| 稳定ID、排除、残差及126屋顶 | 通过：98处地标排除、401个父体残差与126处有据屋顶；屋顶实际解码三角精确保留 |
| 文件上限、SHA、几何与清单 | 通过：169,320个near与1,708个far的结构、SHA及存储/解码大小检查，单文件均小于100 MB |
| 实际网页加载、切换与失败恢复 | 通过：外滩与普通楼片区切换、近景要素遮罩及俯瞰恢复正确；异常加载恢复另由完整自动测试覆盖 |

清单与全部1,708份READY记录已对账，计169,320个near文件、1,796,419个要素；最大far为1.88 MB。见[清单大小核对](../../../data/audit/city-detail-v5/release/manifest-size-summary.json)。此核对仅读取元数据，文件内容、SHA、几何与网页验收以上表最终审计为准。

[完整运行时测试](../../../data/audit/city-detail-v5/release/runtime-tests.json)已通过，覆盖加载取消、迟到结果释放、资源计数和近远归属；网络期限回归见[修复记录](../../../data/audit/city-detail-v5/release/network-deadline-fix.json)。[实际浏览器验收](../../../data/audit/city-detail-v5/release/browser.json)已通过外滩及普通楼片区的加载、移动、遮罩切换与俯瞰恢复；该流程并未逐栋浏览全市模型。街景超时预算回归见[修复记录](../../../data/audit/city-detail-v5/release/street-timeout-fix.json)。

## 许可

原创生成代码与构件采用项目MIT。Overture / OpenStreetMap轮廓和派生数据库按ODbL-1.0保留来源、版本和署名；高度数据沿用CMAB、CNBH、GHSL等原有CC BY 4.0记录。表面表现若使用Poly Haven扫描样本，按原CC0来源清单署名。本生成器没有把照片裁成普通楼的真实窗户纹理，也没有从未知来源补入模型。
