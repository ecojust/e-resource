# 从冻结源码重建包玉刚图书馆

当前作者版本为`geometry-v2`。`source-freeze.json`列出的26个文件必须保持原始相对路径和原字节，包括两张CC历史照片和自制平面草图；构建器保存raw前会校验全部条目。资产目录中的参考照片只是另一个原字节引用，不能代替源码`references/`中的文件。

源码检查环境为Python3.12.14、NumPy2.3.5、Shapely2.2.0。原生脚本使用Blender的glTF导入器和Cycles CPU；实际渲染环境、版本和相机以交付审核中的`native-render-report.json`为准。模型代码不读取或嵌入2021私有参考图。

从本目录运行，并选择全新的输出目录：

```sh
python build_model.py --out /tmp/baoyugang-rebuild-v2/raw
python build_model.py --lod --out /tmp/baoyugang-rebuild-v2/authored-lod
blender -b -t 2 --python render_previews.py -- --glb /tmp/baoyugang-rebuild-v2/raw/minhang-baoyugang-library.glb --output /tmp/baoyugang-rebuild-v2/native --samples 24 --threads 2
```

`--lod`仅删除`fine-tile-joints-N`实体细缝，保留所有其他构件。实际web/LOD压缩和注册需要另行交付的独立工具冻结、实际解码及审核链，不能用上述作者构件小测替代。

当前模型重建仅依赖本源码布局及上述软件；历史坏例诊断脚本`history/diagnose_v1_caps.py`是可选审计工具，重放它还需要原v1 raw和原生截图档案。完整历史检查报告与小型失败账本保留原SHA，不将旧报告的raw哈希替换成新版本。

每个输出文件必须严格小于100,000,000字节。作者工程预算为raw<45MB、native<30MB；web预算<20MB由后续打包检查执行。层高与整体27.4m均是重建估计，不是实测精度认证。
