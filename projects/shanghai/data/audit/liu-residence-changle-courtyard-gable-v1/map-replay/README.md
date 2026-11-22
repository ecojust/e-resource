# 刘氏花园住宅庭院山墙的地图复核

长乐路784、786号住宅的庭院山墙落在原建筑4658。程序在320期城市目录和321期正式接入的目录中分别验证同一组几何。地面测试覆盖33处庭院、墙内和凸窗采点，并检查每种加载状态下的12栋邻屋。真实矢量瓦片的分件38934830/43保存了这处山墙的裁剪结果。

在项目目录启动相应时期的冻结站点后，从本目录运行下面的命令。Node.js 需支持 module.registerHooks。第一个参数选择城市时期，第二个参数是放置文件，第三个参数是带有正式manifest.json的四件模型目录，最后一个参数指定结果文件。

```sh
node check-runtime.mjs 320 ../final-placement-contract.json ../../../../assets/models/candidates/jingan-liu-residence-changle-courtyard-gable run-320.json
node check-runtime.mjs 321 ../final-placement-contract.json ../../../../assets/models/candidates/jingan-liu-residence-changle-courtyard-gable run-321.json
```

程序默认访问本机31320或31321。其他站点通过SHANGHAI_CITY_ORIGIN指定完整地址，末尾保留斜线。SHANGHAI_COMPARISON可指向该期带签名的比较文件，SHANGHAI_PROJECT_ROOT可指定项目根目录。输出记录实际HTTP字节数与校验值、近远两档三角面数，以及装载前、近档、隐藏、恢复、远档、卸载六个状态的裁剪、行走和显示结果。
