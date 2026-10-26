# 复现与验收顺序

当前文档为geometry-v2待验收草稿，不宣称任何新模型输出已通过。公开包必须保留source-freeze.json所列59项在作者根目录中的原相对路径，包括references下的五张CC图和字体许可；资产参考目录中的同图副本不能代替这些依赖。

在仓库根目录进入作者源码目录，然后使用新的输出目录：

```bash
cd source/precise/jiading-shanghai-auto-museum
python -m pip install -r requirements.txt
python run_root.py --verify-only
python run_root.py --raw-output /absolute/new-run/raw
```

Python3.12、NumPy2.3.5和Shapely2.2.0用于原始生成。全部字形轮廓和局部修复输入已随包提供，完整生成不访问网络、不要求系统字体、MAIN或历史v1模型。prepare_repairs_from_v1.py是可选证据输入再生成工具；只有主动重做这项历史诊断才需要另外提供原v1 raw及sidecar，并校验其固定SHA。

独立实际raw检查应先确认全部分件闭合、方向/法向、原构件保留、唯一改动面板和五新增构件接合，以及新增北连接件不封堵五槽。源码的13个小夹具不能替代完整导出模型检查。

随后由Blender4.3.2导入真实当前raw，生成native与三个视角：

```bash
blender -b -t 2 --python render_previews.py -- \
  --glb /absolute/new-run/raw/jiading-shanghai-auto-museum-raw.glb \
  --output /absolute/new-run/native --samples 48 --threads 2
```

full为1.7米眼高45mm透视并以实际模型包络适配；detail/rear沿用v1正交相机。相机未照片标定。native生成标志、人审记录和实际PNG均须保持真实状态，不能将生成完成等同于视觉通过。

Web/LOD由另行冻结的新工具修订执行无损meshopt压缩（gltfpack -cc -noq -km -ke）。实际解码必须逐三角验证位置、材质和受限法向，并重新执行对应有限几何问题。打包、注册draft、网页第三人称检查与发布属于后续独立步骤；本草稿未自动执行它们。
