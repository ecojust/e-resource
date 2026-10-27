# 巴金旧居主楼：可复现模型源码

此目录对应仓库项目内的 `source/precise/xuhui-bajin-residence/`，包含模型生成源码、程序材质与公开复现清单。模型描述武康路113号主楼外观：卵石抹灰、南侧折线山墙与拱形阁楼窗、北侧拱廊入口。附楼、园门、花园、邻楼及室内不在建模范围内。

2.20m门扇高度是建模先验；约12.3317m模型包络高度、隐藏北屋面、侧墙、台阶及矮墙前凸均含推估，不是测绘结果。位置锚点固定为 `[121.43606524072175, 31.21051863775041]`，朝向烘焙为GLB East/Up/-North，ground与rotation均为0。

## 生成模型和程序材质

以下命令均从本目录运行，无需原始研究目录、私有照片或网络。建议使用独立工作副本。复现实测环境为Python 3.12.14、NumPy 2.3.5、Shapely 2.2.0、Pillow 12.3.0；原生文件使用Blender 4.3.2。

```sh
python -m pip install -r source/requirements.txt
python source/generate_material.py --output textures
python source/build_model.py
```

输出为 `exports/bajin-main-detailed.glb`、`exports/bajin-main-lod.glb`、三张程序PNG及 `textures/MATERIAL.json`，另生成结构和属性清单。安装依赖可能需要网络；具备所列依赖后，生成过程本身不需要网络。模型生成只读取当前目录内的源码、数值输入与程序纹理。

需要原生文件与预览时，先创建输出目录，再运行：

```sh
python -c "from pathlib import Path; Path('review/previews').mkdir(parents=True, exist_ok=True)"
blender --background --threads 2 --python source/render_native.py
```

原生文件输出到 `review/native/bajin-main-house.blend`，预览输出到 `review/previews/`。渲染包含独立预览地面、灯光和相机集合，它们不是建筑或庭园资产。本次公开布局验证没有重新执行耗时的原生渲染；原生文件来源另由资产元数据记录。

## 生成WEB和LOD编码

安装gltfpack 1.3并加入PATH，使用尚不存在的输出目录：

```sh
python source/encode_web.py \
  --raw exports/bajin-main-detailed.glb \
  --lod exports/bajin-main-lod.glb \
  --out web
```

如程序不在PATH，可增加 `--gltfpack /your/install/path/gltfpack`。编码使用 `-cc -noq -vtf -vnf -km -ke`；保留原始copyright/extras和PNG字节，不做位置/UV量化，不增加TANGENT。输出位于 `web/xuhui-bajin-residence-web.glb` 与 `web/xuhui-bajin-residence-lod.glb`，同时报告实际字节、SHA及面数。加载器须支持 `EXT_meshopt_compression`。

`PUBLIC_REPRODUCTION.json` 绑定本公开布局的源码、README和八个预期生成结果；`PUBLIC_VALIDATION.json` 记录在临时隔离目录中的实际重建及编码比较。两份记录不代表浏览器或发布验收。

`provenance/PORTABLE-v2.json` 原样保存原冻结源模型的清单，仅作为历史来源记录。其README和旧目录记录不用于校验本公开布局；请以新的公开复现清单为准。`source/check_revision.py`、`source/write_handoff.py` 等历史审查工具需要额外的审查记录，不属于上面的模型/材质/编码生成流程。

## 来源、材料与许可

建模和程序材质由agent创作，使用MIT许可；源轮廓背景保留OpenStreetMap contributors / CMAB的ODbL-1.0归属。三张512px卵石抹灰PBR图覆盖0.40m重复单元，是原创建材近似，不是现场扫描，也不读取照片像素。

公开照片参考为Jpbowen的两张CC BY-SA 4.0作品：[花园立面](https://commons.wikimedia.org/wiki/File:Ba_Jin_house,_Shanghai.JPG)、[北入口](https://commons.wikimedia.org/wiki/File:Ba_Jin_house_front_door,_Shanghai.JPG)。照片不是模型纹理，详见同目录的公开来源登记及其实际发布的参考文件。模型、编码、集成及浏览器接受状态由外部验收记录分别说明。
