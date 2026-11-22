# 工部局电气处工字楼门廊的原城复算

在仓库根目录运行 `python projects/shanghai/data/audit/electricity-department-residence-porch-v1/map-replay/replay.py`。程序使用 Python 3.10 以上版本、Shapely、Node.js 24 和项目 vendor 目录的 Three.js、Meshopt 与 MapLibre。

第318期的第353版原始城市目录中有313条候选建筑记录。地面复算从这份原始目录和已冻结的建筑足迹出发，逐项检查21个相邻建筑、22个地面点和2157号原建筑保留部分。门廊占用范围见上一级的 final-placement-contract.json。

相机复算使用当期31318实际提供的远景和近景三角网。程序读取已归档的原始响应，在本机临时端口重放，分别复查两种细节等级下建筑物与相机视线的交会。公开记录保留了现场原始网址、字节数和 SHA-256。input-digests.json 分别列出原始城市目录、完成第31层处理的目录和所用库的签名。
