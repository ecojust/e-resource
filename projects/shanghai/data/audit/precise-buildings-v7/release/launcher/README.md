# 23项导航启动包实际验证

应用固定提交：`53ee12a60fcd613d82f73cb50cdf0b36436052eb`。ZIP为 **75,069,903 bytes**，严格小于100 MB；SHA256：`6ba119780b3e81b9965ab4fa75cd07c9009be51b7137f25558a9ae00f8dcab5c`。

[构建记录](build-report.json)与[独立归档检查](archive-check.json)核对284个ZIP条目的CRC、283个清单成员的原始字节/SHA、安全解压路径及固定提交URL。解压应用含23项导航、2个完整普通建筑目录宏和4栋普通建筑；包内25个GLB，其余建筑与全市分块按需联网加载。

[实际解压浏览器](qa-qingpu/browser.json)使用本次ZIP的真实解压结果，验证青浦北大街222号与208–212号茶楼的静态复用、动态加载/释放/返回、错误索引回退；[root视觉报告](qa-qingpu/visual-review.json)记录实际查看的10张截图并绑定本ZIP及应用提交。输入见[inputs](inputs-qingpu-zip.json)。全部三阶段通过，返回画面没有目标旧方楼覆盖精模。

武康129/210和青浦两组此前已在完整应用中分别通过[两宏目录验证](../../catalog-acceptance-v3/release-proof.json)。此次ZIP仅选择青浦作为代表宏，没有再次运行武康ZIP浏览器。归档的URL/SHA链与[公开文件逐字节核对](public-app-verification.json)覆盖武康新增模型资源；它们不冒充未执行的浏览器验证。

公开核对实际读取57个响应、66.99 MB，包含新增两栋的raw/web/LOD/Blender八文件、应用代码、目录元数据和固定提交的githack HTML；未保存下载副本。[主项目资源检查](main-assets-check.txt)通过，最大检查文件76.88 MB；该轮明确复用已冻结全市审计，没有重新审核全部城市分块。

[解压运行时快照](extracted-runtime-snapshot.json)绑定包内两份更新的JS，归档检查在浏览器启动前已核对全部解压文件。没有在包内声称存在已排除的测试或package文件。

完整解压后进入shanghai目录运行 `python -m http.server 8000`，浏览器打开 `http://localhost:8000`。城市地图和未缓存模型仍需联网。包内v6.0标识沿用现有归档格式；实际内容与本页所列固定提交、23项导航及校验值对应。

照片覆盖不到的背面与部分尺寸含推定，周边普通建筑仍为既有参数模型。本验证不代表全市逐栋照片复原、所有行走角度或硬件帧率验收。
