# 百代小楼与公园底图

以北墙中点作原点，将三档公开模型投到衡山路811号的原建筑1982，分别读取城市底图近档和远档。沿0.5米网格垂直求交，另在六个高度对三角网格切面取闭合轮廓。近档建筑包含装饰和开口，切面围出的面积只描述该高度的实物截线。1971号和779号是75米范围内的另外两栋原建筑。

两幅航片不同年代的拍摄角度与侧移影响屋瓦的落点。aerial-controls.json记录在550×490显示图上亲读的瓦面内部多边形、原图SHA与原始服务坐标。标注区外含被树冠遮挡的边缘。原影像按各提供方的使用条款另取。

在项目目录运行以下命令。输入清单列出每个实际GLB、压缩和图形库入口对应的固定提交。

```sh
D=source/precise/xuhui-pathe-records-office/measurements/city-contact
python "$D/measure.py" --project . --output ./pathe-model-sections.json
python "$D/roof-evidence.py" ./pathe-model-sections.json ./pathe-roof-points.json
```
