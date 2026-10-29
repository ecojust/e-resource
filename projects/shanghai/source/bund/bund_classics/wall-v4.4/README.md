# 外滩2、3号：v4.4结构墙共形并集

本包修复原结构墙由独立盒子拼接而留下的内部共面侧面。它只替换源码允许的0.45m厚石墙盒，保留现有窗口/拱顶、柱与雕饰、窗框、屋顶、真实平面轮廓及地理坐标。建筑高度、各层分配和未见立面的原有推定性质不变；这不是新增的测绘或摄影测量成果。

原墙盒的接触面会形成沿墙高度方向的重复内部表面；相邻墙单元现在共用一套u/z网格顶点，只有真正的墙体边界输出侧面。父流程已经用同机位、同光照的纯Three前后画面对照，确认长竖线消失且可见建筑构件保留。

## 冻结输入与许可

`baseline/bund02.blend`、`baseline/bund03.blend`为修复前已经发布的原生模型，SHA256与原建筑清单一致。`baseline-manifest.json`保留两者哈希、字节数和完整原导航记录。`footprints.json`为原始冻结建筑平面。重建程序每次校验输入原生文件的哈希；默认直接使用包内基线，不依赖工作区中的旧资产路径。

原模型与代码：©2026 桔子桑，MIT，见随附LICENSE。平面来源：©OpenStreetMap contributors，ODbL1.0。原照片仅作为建筑造型参考，没有贴入这些模型：2号为Legolas1024的CC BY-SA3.0照片，3号为Suicasmo的CC0照片；作者、原图URL和许可URL保存在原导航记录，并写入所有输出GLB的`asset.copyright`。照片许可不因源代码使用MIT而改变。

## 重建

已验证版本为Blender4.3.2与gltfpack1.3。将本包放在项目的`source/bund/bund_classics/wall-v4.4/`，从项目根目录执行：

```sh
for building_id in bund02 bund03; do
  blender --background -t 1 \
    --python source/bund/bund_classics/wall-v4.4/clean_wall_baseline.py -- \
    --id "$building_id" \
    --output "exported/wall-v4.4/$building_id-clean.blend" \
    --raw "exported/wall-v4.4/$building_id-raw.glb" \
    --report "exported/wall-v4.4/$building_id-wall-validation.json"

  python source/bund/bund_classics/wall-v4.4/compress_models.py \
    --id "$building_id" \
    --input "exported/wall-v4.4/$building_id-raw.glb" \
    --output exported/wall-v4.4 \
    --gltfpack /path/to/gltfpack
done

python source/bund/bund_classics/wall-v4.4/check_rebuild.py \
  --output exported/wall-v4.4
```

独立复制本包也可执行这些程序，只需调整脚本路径；生成器仅依赖Blender内置Python/`bpy`。压缩脚本使用普通Python标准库和gltfpack。`--input`可显式指定冻结基线的另一份副本，但哈希仍必须匹配。

完整网页模型严格使用`-cc -noq -km -ke`，远景LOD追加`-si 0.35 -se 0.002 -sp`。两者都不进行位置量化；LOD另外进行网格简化。gltfpack1.3会丢弃`asset.copyright`，所以脚本在每次压缩后恢复完整来源声明。不要绕过这个步骤只运行裸gltfpack命令。

## 实际输出与验证

| 建筑 | 原始GLB | 网页GLB | LOD | 完整/LOD三角数 |
| --- | --- | --- | --- | --- |
| 2号 | 3.86 MB | 1.49 MB | 1.03 MB | 74,562 /41,160 |
| 3号 | 9.74 MB | 3.71 MB | 1.72 MB | 172,401 /70,534 |

所有单个文件小于100 MB。共形网格需要分割前后墙面，因此完整模型三角数略增；LOD目标比例0.35不等于实际最终比例。各模型实际解码包围盒与原清单相同，LOD包围盒最大变化均为0m，但这不代表LOD内部网格未简化。

`release-manifest.json`保留六份raw/web/LOD的最终哈希、三角数和实际解码边界。`validation/`保留原生面保留证明、独立raw检查、压缩检查和便携重建结果：

- 2号734个、3号1,004个结构墙盒被替换；其余64,214 /141,865个原面及其索引、材质、平滑标志和全部原顶点坐标保持不变。
- 未替换材质的有向三角位置、法线和材质定义精确一致；窗洞/拱形轮廓经前墙面域差异及双向80微米容差覆盖检查。
- 所记录中层范围内的相反共面侧面交叠面积分别从526.4722 /580.8813m²降为0。
- 全部新墙组通过闭合边、相反绕序与正体积检查。顶点归并实际最大约3.34 /4.93微米，属于数值修复，不代表现场测量精度。
- 使用项目实际GLTFLoader/MeshoptDecoder检查，完整raw/web有向三角位置精确相同。法线最大方向差分别0.021431° /0.022918°，均小于0.05°容差；法线不宣称逐位无损。
- 仅使用包内冻结输入重新生成后，六份raw/web/LOD文件均字节相同。`.blend`容器会随Blender保存状态/路径变化，不要求其文件哈希重现；它导出的raw几何与已发布结果字节相同。

根项目的实际解码压缩检查可另行运行：

```sh
node tools/qa/compare_model_compression.mjs . \
  exported/wall-v4.4/bund02-raw.glb \
  exported/wall-v4.4/bund02-web.glb \
  exported/wall-v4.4/bund02-compression-check.json
```

将2号换为3号可检查另一栋。此包不自动改写地标清单、模型路径或Git仓库。集成时使用随附每栋资产元数据，保留原`height_m`、锚点、起步点、朝向与LOD切换距离。
