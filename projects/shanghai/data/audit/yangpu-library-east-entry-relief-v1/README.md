# 原上海市图书馆东门修订核验

2019年的门面近照、另一位作者刊出的黑白老照和2018年的整面照片，可用门上石阳台、两侧八角窗及成对灯具定位至长海路一侧的双扇外门。照片提供三角花孔、云形下扇和券带石花的组合，细小卷草及浮雕深度按图概括。杨浦图书馆的原入口、地块1196和两个内院沿用V13的整馆模型。[建筑及署名](../../../source/precise/yangpu-library/revisions/east-entry-relief/README.md) · [三组照片与日期](../../../source/precise/yangpu-library/revisions/east-entry-relief/reference-review.json) · [四项交付](../../../source/precise/yangpu-library/revisions/east-entry-relief/manifest.json)

| 实际模型 | V13 | 门扇与券带修订后 | 修改区外逐面相同 |
| --- | ---: | ---: | ---: |
| 完整馆体 | 365,524 | 390,432 | 363,626 |
| 远景馆体 | 122,688 | 139,556 | 121,136 |

两个档位的全馆分别与V13成品逐材质核对三角顶点及绕序。围住改动处的边界长0.68米、宽6.23米、高4.13米。含两院、屋顶、扩建馆和其他三面的全部外部三角面均保持相同。分别使用原始及解码后的近远四组几何，做了88次射线取样，可测到深置玻璃、镂孔间的实心窗格、凸出的金属花饰、门槛和两处露天内院。[V13逐面对照](geometry-revision.json) · [实际解码和射线](meshopt-surfaces.json)

Blender 4.3.2重新打开交付工程后，核得四组可编辑的局部门饰顶点，390,432面与原始GLB的坐标、绕序及材质一致。在相同灯光和7.18米宽镜头下，原版外门上部为交叉直条，修订版可以分辨成排花孔、下扇云纹和环绕门楣的石花。[原生工程比对](native-meshes.json) · [同机位原门](east-entry-before.png) · [同机位修订门](east-entry-after.png) · [照片与渲染判断](visual-review.json)

独立浏览器用同一WebGL镜头载入V13与新版本的实际压缩GLB，分别记录完整和简化档、主入口近照及整馆图。每次均核验所收字节和SHA-256、模型面数及渲染上下文。[完整档原门](webgl-before-full-door.png) · [完整档修订](webgl-after-full-door.png) · [远景档原门](webgl-before-lod-door.png) · [远景档修订](webgl-after-lod-door.png) · [完整馆体](webgl-after-full-whole.png) · [浏览器收据](isolated-browser.json)

登记程序在122处的父版本上只更新既有普通模型的三份记录、街区索引的校验值和顶层普通模型目录指针。第二次执行及只读核验所得五份文件逐字节相同。原地标ID与可步行入口沿用原记录。[登记程序](register-revision.py) · [五份登记与文件指纹](registration-check.json)

修订后的122处地图逐一请求了362份正式场景输入，共242,630,905字节。索引从普通模型目录逐级指向新版东门，候选模型清单维持同一签名。[地图全部请求、字节和校验值](final-http-inputs.json)

本版同时更新了开发用的地图校验脚本，可读取两种原始地块记录所用的坐标字段。东方饭店、女青年会和虹口救火会以档案中的真实地块重跑后，均检查到了相应的城市矢量面与地面阻挡区。[三栋实测与百乐门对照](../hongkew-fire-station-v1/owner-vector-runtime-check.json)

两次场景之间，董家渡天主堂的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有243组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了14个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收46,156,279字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

在122处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对14个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)

两代均从原有普通地标入口实开城市地图。122个灯牌保持同数，新近、远景实际显示390,432和139,556面；旧V13的365,524和122,688面也在同机位取得。每次均实收六项签名。[真实主图对照](city-map/README.md) · [四件与目录的实际下载](download-http.json)
