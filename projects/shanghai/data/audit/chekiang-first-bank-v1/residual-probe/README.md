# 浙一大楼局部替换的矢量检查

江西中路银行门扇落在被精模替换的西侧墙带内。作者坐标原点落在保留的办公楼内。旧检查把所有局部模型的原点视为必须剔除的样点，在浙一大楼得到一次假失败。这个修订允许在模型自己的 map-case.json 中用 `residualCutProbe` 提供被剔除的局部米制坐标。显式样点须同时位于原建筑和裁切区域内。缺省时仍使用原点。

实测采用原国华银行149处阶段和原浙一大楼154处阶段。国华银行原程序及修订程序的全部数值、几何和地面结果相同，仅检查器自身指纹不同。浙一大楼采用西侧银行门的样点后，两种底图来源分别保留了一份办公楼余面，作者原点在两份余面内，银行门在两份余面外。将显式样点故意移回原点，两条前置条件中的裁切范围检查正确报错。原始失败输出、修改的程序片段和实际数据见 [原始错误](original-failure.log)、[补丁](checker.diff) 和 [对照结果](regression-results.json)。

在项目目录运行以下命令。两个目录参数均指构建时对应版本的 projects/shanghai，含当时的目录、底图摘要、程序和审计文件。

```sh
python -B data/audit/chekiang-first-bank-v1/residual-probe/check-regression.py \
  --legacy-project "$GUOHUA_PROJECT" --target-project "$CHEKIANG_PROJECT" \
  --revised-case data/audit/chekiang-first-bank-v1/map-case.json --out "$RESULT_DIR"
```

单独应用同一改动可运行 `python -B apply.py <检查器文件路径>`。程序仅修改传入文件。两棵历史发布树及其原始清单保留了各自检查时的字节。
