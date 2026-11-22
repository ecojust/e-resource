# 东平路11号南坡三座老虎窗与原城屋面

在上海项目目录用 Python 3、NumPy、Shapely 和 Node.js 执行以下命令。signed-files.json 列出原始城市网格、三档本体和解码工具的固定版本。原城和窗带的距离与高度均以米计。

```sh
python source/precise/xuhui-dongping-eleven-mansard-dormers/measurements/roof-contact/measure.py --project . --output roof-and-dormers.json
```

每档选南檐内移0.65、1.65及2.65米三个位置，在每处取沿檐71点、跨坡9点的竖向剖束。侧面和居中的三座窗头取自同一片坡屋面。窗间未设窗头的部分另算原屋顶和瓦面高度，用中位高度差拟合单一标高。输出旁的 roof-and-dormer-rays.json.gz 保留5751束逐次交点以及原户范围判断。

本次现场和首次公开的地块记录将原目录来源分别写为完整站址和相对文件名。两份记录逐字段比对后，其余字段、原网坐标和对应户号均相同。重作时可核对解压后的探束摘要及原户各组数字，独立进程编号会随运行更新。
