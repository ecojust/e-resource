# 上海汽车博物馆 V11 geometry-v2 作者包

这是可复现的局部修复源码，尚未生成或验收完整geometry-v2模型。v1原生三图已查看，五处局部缺接合使其仍未接受；见REPAIR-DESIGN.md和change-scope.json。正面朝西侧前场，高体在北、低翼在西南；依据实际地图、水域和五张已查看照片，精确相机仍未标定。

五层、官方历史名义高度32.45米和建筑材料有主资料支持。结构最大悬挑存在15米/17米两种名义口径；局部曲率、退台、层高、坡道和楼梯仍是登记过的估计。见`DESIGN.md`与`calibration.json`。

## 复现

原始模型需要Python3.12、`requirements.txt`中的NumPy/Shapely。读取本包所有几何与字形输入，不访问网络、不要求MAIN或系统字体。

```bash
python run_root.py --verify-only
python run_root.py --raw-output /absolute/new-run/raw
```

原始GLB及语义分件记录生成后，应先独立审核实际Float32三角形。随后由root用Blender4.3.2生成可编辑native及三个视角（full为1.7米眼高45mm透视，detail/rear保持v1正交相机）：

```bash
blender -b -t 2 --python render_previews.py -- --glb /absolute/new-run/raw/jiading-shanghai-auto-museum-raw.glb --output /absolute/new-run/native --samples 48 --threads 2
```

各输出必须使用新目录；此前尝试和证据保留。原生图为示意相机，不能当作已标定照片或自动通过。

## 检查与体积约束

`source_preflight.py`只验证语法、曲线输入、7个小型闭合构件和保留邻居的估计平面距离，没有生成整栋模型。完整raw的结构、接触、负空间、玻璃槽、门、曲面接缝、LOD解码和浏览器均需独立检查。

raw目标小于45MB，native小于30MB，web小于20MB，所有单文件严格低于100MB。采用保留Float32位置的无损meshopt压缩（gltfpack -cc -noq -km -ke），不对整栋做会合并细构件的简化或位置量化，保护实体字形的小三角面。必须保护银框圆卷、五条曲玻璃槽、深檐、分层幕墙、门净空、饰带转折、遮阳间隙、坡道、楼梯和开敞护栏。实际解码后重新验证，不能按源码自检结果放行。

`source-freeze.json`列出全部公开依赖及SHA。`common/photo_architecture.py`是本地实际副本，增加了透射玻璃、唯一分件名和导出三角形范围，运行不依赖旧V10目录。`references/`只纳入5张获CC许可照片、事实摘要、字形数据与许可；未授权官网全文、PDF、厂家/TJAD照片和历史工作目录不进公开交付清单。

模型署名agent，CC BY-SA4.0；代码MIT；地图源ODbL；照片及字形按各自许可，见`MODEL-LICENSE.md`与`references/ATTRIBUTION.md`。未修改MAIN、旧模型或Git。

新增repair-inputs.json是明确交付的几何输入；完整构建不要求旧raw。check_local_repairs.py仅生成6个小型源码夹具并与实际v1目标比较，不能替代独立actual v2审核。原设计草图与v1源码检查记录保留其当时SHA，不作为v2通过证据。
