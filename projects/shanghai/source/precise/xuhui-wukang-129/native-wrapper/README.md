# 展示地面 −0.01m 的冻结native入口

`finish_native.py` 为已生成v2 native所用适配器的原字节副本，SHA256：`01f758735e364a6370dcba2f31167ea4c574a154dc77141241f602665f0f27f2`。它锁定本模型raw、`common/blender_finish.py`、相机入口、相机锁和几何输入；只在内存修改展示平面高度，不改建筑或冻结文件。

本发行布局将脚本放到模型源目录内，所以总是显式指定 `--candidate-root /absolute/path/to/model-source`，不要依赖适配器的历史默认兄弟目录。普通Python `--check` 不执行Blender；完整命令、版本、侧车报告和相机步骤见上级 `REBUILD_STANDALONE.md`。
