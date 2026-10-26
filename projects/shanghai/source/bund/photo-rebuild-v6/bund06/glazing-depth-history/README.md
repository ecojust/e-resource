# 玻璃深度修订前的源码

这些快照只对应旧原始 GLB `2e79827911adc35861cd4603d15204335e334727b10d4c5b8e5288498bfeafc3`。旧 README 保存在 `README.before-glass.md`，旧原生预览记录不代表新模型验收。未改动的照片、控制点与公共生成器仍从上一级源码取用；`baseline-source.json` 给出全部原始输入 SHA256。

在完整源码目录中执行：

```bash
python source/bund/photo-rebuild-v6/bund06/glazing-depth-history/restore_previous.py --output /tmp/bund06-before-glass
python /tmp/bund06-before-glass/bund06/build_model.py --output /tmp/bund06-before-glass-output
```

恢复工具会先核对全部输入，再写入一个必须尚不存在的新目录，保持 `bund06` 与 `common` 兄弟目录关系；不会修改当前源码。恢复审计只验证旧输入逐字节一致，不宣称重复生成或渲染了旧模型。公共文档历史清单如有旧说明 SHA，以本次实际冻结的 `baseline-source.json` 为恢复依据；生成器与照片本身未改动。
