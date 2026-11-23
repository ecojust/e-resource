# 襄阳南路313号修缮后住宅院面

上海市第五批优秀历史建筑5D103登记为襄阳南路313号，住宅、局部办公。修缮记录记载院内建筑现有三层、建筑面积364平方米。2015年与2020年的街景能区分311号邻门与313号院门。三处街面折墙窗位的独立交会落到原城市对象3304的外墙。[登记与影像来源](SOURCES-LICENSE.md)

施工单位刊载的两个修缮后拍摄机位分别清楚展示凸出的四扇二十格窗墙及另一面的青色遮雨篷。照片中的开合、近处遮挡和画幅范围各不相同。施工图1采用凸墙大窗的中轴作局部X原点，以凸墙外皮定Y0，向院内为正。照片的物理尺度采用约3.0米的层高先验，尚无实测层高。

从仓库根目录运行以下命令生成两档模型，检查每个构件的闭合方向与正体积。

```sh
python -B projects/shanghai/source/precise/xuhui-xiangyang-313-restored-courtyard-fronts/measurements/check_mesh.py /tmp/xiangyang-313-mesh
```

[施工照片机位](measurements/courtyard-cameras.json) · [大窗二十格的读数](measurements/large-window-readings.json) · [门牌与街侧窗的核位](measurements/numbered-courtyard-and-street-windows.json)
