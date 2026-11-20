# 百乐门舞厅的地块、几何与浏览器验收

模型重建了愚园路218号历史舞厅的弧形入口、万航渡路及愚园路两翼和分层圆灯塔。完整模型31,078面，远景模型15,586面。2025年刊出的修缮后夜景确定当前招牌形式，较早街景和三期屋顶影像补足体量关系。[来源与历史沿革](../../../source/precise/jingan-paramount-ballroom/README.md) · [独立模型](../../../paramount-ballroom.html)

冻结街坊中，具名目标地块857包含11,680个近景三角面和40个远景三角面。实测裁剪覆盖了两档原楼。最近的其他近景几何与新楼相距2.60米。含邻近百乐门大都会楼的另一组有116,900个近景三角面，最近距离28.39米。碰撞轮廓沿三处门口退至门扇，西侧两翼之间与两边街道留给行人。[近远景独立量测](placement-geometry.json) · [配准参数](final-placement-contract.json)

三档外观的射线检验覆盖三处玻璃门、上方竖窗、两块红字牌、两翼开窗与四层灯塔。原始GLB、近景及远景均按实际解码结果核验。[实体射线](surface-checks.json) · [Blender重开与压缩对照](geometry-native.json)

本版修复精细城市底图首次下载超时后长期停留在粗略底图的问题。普通底图可先显示，后台随后重试一次精细目录。[两栋既有建筑的现场记录与实际 HTTP 前后对照](city-detail-recovery/README.md)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有225组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收5,688,082字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

正常冷开由手机目录触选百乐门，随后用同一浏览器在桌面尺寸重载。117处对照与118处后态的五个城市视图、16个地面见证及单体页的四份实取下载全部通过。[117处对照](control-browser.json) · [118处地图](main-browser.json) · [独立页](viewer.json) · [逐图核对](map-visual-review.json)

故障试验首次只发送32字节，约25秒后应用取到粗目录，再自动请求完整精细目录。原页面中实际可见宏的字节从681,132增为1,296,608，百乐门在两时点均可见。初轮脚本使用短组名，近景组附加断言超时，原始末态另证宏替换已发生。[首次网络与页面的原始记录](city-detail-recovery/first-map-run/cold-map-directory-recovery.json) · [已完成观察与探针限制](city-detail-recovery/first-map-run/observed-recovery.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 36 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/d389ef3f573fcae47be06493062cac949895d2d1/projects/shanghai/index.html#landmark=jingan-paramount-ballroom&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 36 项时，有 11 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
