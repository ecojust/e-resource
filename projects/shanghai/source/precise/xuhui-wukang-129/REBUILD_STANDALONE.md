# 武康路129号 v2 独立模型包复建

此目录完整保留40个冻结模型源文件，使用本地 `common/` 副本，不依赖外滩共用源码目录。当前 raw SHA 为 `c0915a9d76761865b4020d31397b8ef66ddb6efc4112bbee150264119754afa9`，190,926 个三角形。原 `MODEL_CANDIDATE.json`、README 与历史报告保留当时“等待视觉复核”的状态；后来完成的有限范围实际视觉复核在 `evidence/visual-review-v2.json` 和 `evidence/root-v2-visual-review.json`。它们不等于全楼实测或网页验收。

模型保持独立交付，未加入20栋导航。两张CC BY-SA 4.0原照片仅用于身份、几何和尺度参考；raw/web/LOD/native均没有照片纹理。原照片仍随来源归档保留署名与许可，不能因为没有嵌纹理就删除来源或改称CC0。隐藏后立面、部分深度、圆端半径、材质和构件细节仍是推定或简化。

## Python模型和相机数值检查

在本目录的可写副本中运行。依赖版本在 `build-environment.json` 和 `packaging/dependencies.json`；模型重建本身不访问网络。`build_model.py` 会写本目录 `calibration-model.json` 和 `output/`，故不要直接在需要保持只读的发行归档上运行。

```sh
PYTHONDONTWRITEBYTECODE=1 python build_model.py
PYTHONDONTWRITEBYTECODE=1 python check_model.py
PYTHONDONTWRITEBYTECODE=1 python photo_camera.py --check --width 1500 --report output/photo-camera-check.json
PYTHONDONTWRITEBYTECODE=1 python native-wrapper/finish_native.py --candidate-root . --check --report output/native-wrapper-check.json
```

最后一条只执行普通Python的SHA和AST预检，不启动Blender。必须显式传 `--candidate-root .`：适配器原默认路径来自历史隔离目录名，不能在新布局下依赖默认值。`check_revision.py` 是对首版的历史差异审计，单独运行它还需要首版源码/raw；它不是当前模型或native复建依赖。

## 完整native与同相机预览

需要Blender 4.3.2。以下用绝对路径，输出必须是尚不存在的native目录；适配器会拒绝覆盖已有native。建筑源地坪仍是0，仅 `Preview_only` 展示平面为 **−0.01m**。适配器在内存中对冻结 `common/blender_finish.py` 仅修改这一条平面创建语句，不修改几何/相机输入文件。

```sh
WUKANG_SOURCE=/absolute/path/to/writable/source/precise/xuhui-wukang-129
WUKANG_NATIVE=/absolute/path/to/new-native-output

blender -b --python-exit-code 1 --python "$WUKANG_SOURCE/native-wrapper/finish_native.py" -- \
  --candidate-root "$WUKANG_SOURCE" --output "$WUKANG_NATIVE" \
  --view-azimuth 307.69525847124856 --view-elevation 12 --width 1500 --height 1000

blender -b "$WUKANG_NATIVE/xuhui-wukang-129-raw.blend" --python-exit-code 1 \
  --python "$WUKANG_SOURCE/photo_camera.py" -- \
  --width 1500 --render "$WUKANG_NATIVE/photo-perspective.png" \
  --report "$WUKANG_NATIVE/photo-camera-run.json"
```

第二条只渲染，不再次保存native。第一次产生的 `xuhui-wukang-129-raw-blender.json` 必须与native同目录且原字节保留，供相机脚本核对native SHA。原交付native按原字节复制到资产路径 `model.blend`；重新生成的Blender文件不承诺容器SHA相同，只承诺使用锁定输入和明确生成步骤。本次源码便携性检查没有再次运行Blender。

## 网页压缩与LOD封装

封装依赖Python/NumPy、`zstandard` 和 gltfpack npm 1.3.0（或相同工具构建）。冻结的通用封装器、基础测量helper和LOD策略都已包含在 `packaging/`；内置 `measurement-project/` 只提供测量脚本，不含其他城市数据、模型或导航。下例在本目录运行，输出指定为本目录之外的全新目录。

```sh
python packaging/package_precise_building.py \
  --spec packaging/package-input.json \
  --raw output/xuhui-wukang-129-raw.glb \
  --native /absolute/path/to/native/xuhui-wukang-129-raw.blend \
  --project packaging/measurement-project \
  --shared-helper packaging/package_building.py \
  --gltfpack /absolute/path/to/gltfpack \
  --output /absolute/path/to/new-standalone-package
```

web参数是 `-cc -noq -km -ke`；LOD沿用冻结的误差与边界策略。raw与native只按原字节复制；web的顶点位置/材质/绕序/三角重数精确保持。导出器处理后的法线允许沿用既有0.05°上限，本次实测约0.01530°，不宣称法线字节相同。LOD是远景简化；边界和洞口采样通过不代表全表面或所有曲线完全相同。

源码清单不包含生成raw、native、web、LOD或缓存；两张许可原图和分析证据保留。每个文件小于100,000,000字节。
