# 真如寺大殿：公开包构建

本说明对应 `putuo-zhenru-main-hall` 的 geometry-v2 公开构建文件。作者原始 README 原字节保留为 `README.author.md`；原作者冻结是历史来源记录，公开包实际文件与研究摘要映射以 `source-package-files.json`、`publication-map.json` 为准。

模型生成器的实际文件依赖是 `build_model.py`、`common/photo_architecture.py`、`calibration.json`、`geometry-input.json`、`references/photo-register.json`。四张参考照片保留原字节及原许可。官方研究 review 和 calibration-review 不被生成器/渲染器读取；其公开事实摘要分别位于 `references/public-official-summary.json` 和 `references/public-calibration-review.json`，不附完整楹联或整页 HTML。没有修改原始构建代码、几何输入、校准、照片登记或图片。

需要 Python 3、NumPy、Shapely 2.1 或兼容的约束 Delaunay 三角化接口，以及 Blender 4.3.2 或兼容版本。请在本源码目录中运行，替换为尚不存在的绝对输出路径：

```sh
python3 build_model.py --output /absolute/new-run/raw
blender -b -t 2 --python-exit-code 1 --python render_previews.py -- --glb /absolute/new-run/raw/putuo-zhenru-main-hall-raw.glb --output /absolute/new-run/native --samples 48 --threads 2
```

生成器输出 raw GLB、构件记录和资产元数据；原生脚本从实际 raw 创建可编辑 blend 与全景、南面细部、后侧三张 PNG。原生预览集合中的地面、灯光、相机没有加入 GLB。后侧属于历史照片与文献约束下的估计，不能称为当前背面测绘。

网页和 LOD 是另外的实际压缩交付，位置及 SHA 见 `delivery-record.json`；本包保留实际所用 packaging spec 与补充解码/注册工具。注册工具重放完整历史评审仍需原始研究记录、实际打包结果和独立人审证据，不能仅靠生成预览创建通过。构建本体不依赖这些私有研究文档。

每个实际输出必须严格小于 100,000,000 字节。源码参数中的目标预算不代替生成后的字节核验。真实有限结构/接触结果、原先失败指标与另行说明保留原报告，不能概括为整栋无碰撞或结构工程认证。


当前修订只允许140斗拱臂/垫座与4斜山脊变化；独立证明显示其余构件的实际位置、法线与材料字节保持。历史8500对瓦片证明仍绑定旧geometry-v1 raw，只通过当前保持性证明沿用其瓦片范围，未在新fullraw重跑。当前木构支承/不露出屋面及4脊/山墙检查另有新证明。原始roles失败、PCA截面失败、B/A检查器诊断与修正记录均按白名单保留，不能将较窄结论扩写成全模型无碰撞。

实际原生复核使用 root-native-visual-review-v2 对应的当前raw/native，且明确full和rear两张斜视都主要看见西侧山墙；几何检查覆盖两侧山墙，不等同于从两个渲染角度都看到了不同山墙。
