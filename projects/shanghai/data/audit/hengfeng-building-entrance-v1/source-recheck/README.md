# 恒丰大楼门罩与柱列

上海市第四批优秀历史建筑名录第4A005项登记为恒丰大楼，地址为江西中路450至454号。Fayhoo 的正面照片可读出「恆豐大樓」题名。照片于2015年1月18日上传，拍摄日期未载。照片署名与许可为 Fayhoo，CC BY-SA 3.0。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [照片与许可](https://commons.wikimedia.org/wiki/File:Heng-Feng_Building.jpg) · [原始来源记录](../../../../source/precise/huangpu-hengfeng-building-entrance/reference-review.json)

桌面和手机各自的相机从两档实际模型检查了题名、柱头、柱身、门罩等12个目标。48道光线均首先击中预期材质，最大深度偏差4.8厘米。两组街区近、远网格另作96次遮挡检查，两个机位均可看到这些目标。[模型逐点结果](../model-sightlines.json) · [街区逐点结果](../actual-sightlines.json)

对第266、267期分别运行两档碰撞检查，每档沿用75个相同的地面位置。门罩新增16个模型障碍点，原街区裁去的三角面数为零。图源建筑为163号，15栋邻屋的原始几何仍在。[前一期地面逐点记录](retained-266.json) · [本期地面逐点记录](retained-267.json) · [测量摘要](results.json)

在含本项目检查工具、Python 依赖和 Node.js 的仓库中运行下列命令。两个参数分别指向第266和267期发行时的 Shanghai 项目根目录，均应含对应的 `src`、`vendor` 和 `data/candidate-city-integrations.json`。程序按 SHA-256 核验五份冻结瓦片资料，并将重算结果与随附的逐点记录比对。

```sh
python reproduce.py --before /path/to/266/projects/shanghai --after /path/to/267/projects/shanghai
```
