# 会斯乐公寓楼梯间钢窗与原有外墙
在上海项目目录使用 Python、NumPy 和 Node.js 运行以下命令。程序从项目模型目录读取第377项三档网格，恢复签定原城的近、远两档；本地缺件从列明的固定提交下载。
```sh
python source/precise/xuhui-georgia-apartments-stair-window-fins/measurements/stair-wall/measure.py --project . --output existing-wall-and-window-lights.json
```
每档模型取横向13列、竖向17行。每一点沿西北外立面的法向分别测原墙和新作的最前侧交面。输出的663行列出材料名、模型面、原近墙面和原远墙面，共1326次比较。坐标沿街向西南为正，标高取两期沿街相机、已知楼梯间线板中心距和人行道联合测定，独立两期的上窗头相差约1.37米。
