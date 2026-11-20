# 圆明园路133号女青年会大楼

上海市房屋管理局第二批名录2A024登记的女青年会大楼，历史使用单位为中华基督教女青年会全国协会。东面七组竖窗、六层街墙和两级退台依据整幅正面与东南斜视照片。右起十三字门额、蓝色长灯、琉璃瓦檐和菱花门楣另有近照。尺寸据图估算，西侧院翼及屋顶机房内构留待进一步取证。[身份、照片及出处](../../../source/precise/huangpu-national-ywca/reference-review.json) · [原生东南视图](huangpu-national-ywca-preview.png)

原始GLB与网页近景各38,806个三角面，远景29,190个。Blender 4.3.2重开98件可编辑网格，13种材质的定向三角面与原始GLB逐层相符。独立解码后，每档45项检查覆盖七组窗的五排玻璃、门后退深、蓝灯、檐瓦、额字、两级退台及门外通道。[四份资产散列与原生复核](geometry-native.json) · [三档独立网格检查](surface-probes.json)

主图仅替换1891号原地块的东临街约12米。北邻149号哈密大楼与133号在城市源数据的共墙位置有约十厘米重叠；与归属不够明确的381个近景三角面均留有间隙。远、近景分别保留原地块60.40%及60.53%的投影面积。两道模型接缝沿原东翼的西侧与北侧闭合，总长40.74米。南侧通道、圆明园路和149号分别保留原有地面或建筑碰撞。[独立原始地块](../../../source/precise/huangpu-national-ywca/footprint-review.json) · [原生远近景与模糊共墙面核验](footprint-review.json) · [配准和碰撞边界](final-placement-contract.json)

117处站点的独立页已在桌面与手机分别通过近、远景切换和四个按散列核验的实际下载。116处对照与117处主图的桌面、手机、街面与邻楼检查仍待实测。[独立页浏览器记录](viewer.json) · [独立页输入与四件资产](viewer-inputs.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有222组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收6,429,874字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

## 主图默认取景

正式116处对照为原底图，117处新版由区目录选择后进入。手机和桌面均显示圆明园路七组竖窗、中央入口与屋顶两层退台。正式站287个输入及4个城市源文件逐一匹配SHA-256，共159,461,535字节。阶段采集时街面、屋顶与远距地面复核仍在进行。[前态](map-before.png) · [手机](map-mobile.png) · [桌面](map-desktop.png) · [阶段收据](default-focus-verification.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 36 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/58e5682ec158782a05ecd61d847a2000fc139afb/projects/shanghai/index.html#landmark=huangpu-national-ywca&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 36 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
