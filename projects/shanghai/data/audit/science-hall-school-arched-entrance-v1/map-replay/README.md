# 上海市科学馆旧址1号楼石券门与山墙小阳台

地表核对使用原单体1524、校园及相邻足迹、检验视线和六种加载状态。319期在独立原网与固定母城间模拟装载，320期从本期真实城市目录装载。两期比较文件保存完整来源指纹。

在包含本项目和相应冻结城市站点的工作区，从本目录运行以下命令。Node.js 需要支持 module.registerHooks。第一个参数可选用 319 或 320。默认读取相应的本机冻结端口。可用 SHANGHAI_CITY_ORIGIN 指定含尾斜线的站点，用 SHANGHAI_COMPARISON 指定相应时期的比较文件。

```sh
node check-runtime.mjs 320 ../final-placement-contract.json ../../../../assets/models/candidates/jingan-science-hall-school-arched-entrance run-320.json
```

程序核对每个输入的SHA、真实矢量切片、图钉、地面与近远网格切换。每份输出包含六个状态与实际 HTTP 字节数。
