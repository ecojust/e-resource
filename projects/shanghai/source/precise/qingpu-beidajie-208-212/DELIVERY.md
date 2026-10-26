# 茶楼v3交付范围

三处真拱洞、开放二层木廊、车木栏杆、六盏灯笼、左竖牌六字、闭合侧山墙和分阶瓦片已建成实体。原生斜视图已实际对照Fayhoo原照片通过：[视图](evidence/native/preview.png)、[原始视觉记录](evidence/native/visual-review.json)、[Blender导入记录](evidence/native/blender-report.json)。这只覆盖本次斜视所见形体。网页材质、第三人称近距离、LOD切换和精模替换生命周期仍由集成验收负责，本文不宣称它们已完成。

[打包记录](evidence/packaging-record.json)保留原始raw/native，输出web 4,593,804字节／199,228三角和LOD 2,669,664字节／90,140三角。四资产最大21,180,492字节，均严格小于100,000,000字节。[实际Three解码检查](evidence/decoded-package-check.json)确认raw/web有向位置与材质三角逐项相同；最大法线夹角0.029496°小于既有0.05°容差。raw/web/LOD边界差为0，三档共90个洞口／廊道内部射线及9个邻接实体墙负控通过。这是有限采样，不是完整LOD表面Hausdorff证明。三档均无嵌入图片或外部纹理。

[离线重建证据](audit/build-reproducibility.json)证明打包前复制出的源码在不访问生产目录、网络或Blender的情况下重建出相同raw SHA。安装后的本目录保留同一build_model.py、geometry-input.json、calibration.json、common、字体和原照片；README仅更正交付状态，差异记录在[delivery-record.json](delivery-record.json)。运行`python build_model.py --output /新建输出目录`后可用`python validate_model.py --glb /新建输出目录/qingpu-beidajie-208-212-raw.glb --output /另存检查.json`核验。字体及第三方数据许可见[COPYRIGHT.md](COPYRIGHT.md)。

压缩复现使用项目`source/precise/tooling/package_precise_building.py`，显式传`--shared-helper source/bund/photo-rebuild-v6/common/package_building.py`和本目录packaging-input.json、raw、native、gltfpack、项目根及全新独立输出目录。该工具保护现有模型目标；已安装仓库复现时可使用一个仅含原字节tools/build_bund_lods.py的空白临时项目作为`--project`，不能删除已安装资产来绕过守卫。输出目录命名为package，其父目录作为`node check_decoded_package.mjs PROJECT PACKAGE_PARENT MODEL_SOURCE`的第二参数；第三参数为本源码目录，PROJECT提供项目vendored Three/Meshopt代码。不同压缩工具版本产生的字节应另行审查。

`audit/`以及`evidence/`内JSON保持原字节，原工作区绝对路径仅是审计来源标识，不是重建所需目录。当前副本定位以delivery-record.json为准。构建阶段`visual_acceptance:false`与原生记录`passed:true`属于不同阶段；check_v3_changes.py比较v2/v3时需要另行提供保留的v2源码，不是raw重建依赖，本交付不重复打包旧模型。

轮廓来自Zenodo East Asian Buildings经Overture收录的真实要素，OSM只佐证地址。7.373m前缘、宏14-13701-6700／local25、同微块27个邻楼约束已冻结。模型采用历史参考照片可见形态，EXIF2016与描述2013冲突未消除；8.187m高度、背面、侧面、屋顶坡度与牌体前移量均非实测。砖色旧化、雕饰、字型和不可见部位有简化，不能称逐厘米扫描或2026现状复刻。
