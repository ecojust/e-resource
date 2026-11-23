# 延庆路121号住宅临街砖墙与凸窗

第五批上海市优秀历史建筑名录列为5D043。2018年2月7日Antigng拍摄的照片记录了长砖墙上的五樘上层窗、红砖腰线和窗下的人字拼砖。西端木筋凸窗坐落在浅券门上，前面两格交叉木筋，折向两侧各一格。[原照片与署名](https://commons.wikimedia.org/wiki/File:延庆路121号住宅.jpg) · [市级名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html)

原点位于券门中心投向长砖墙面的地面点。2015年的多个街景机位给出西端相邻窗台中心距约2.7米，上下两层窗台高差约3.5米。券口净宽约2.12米，小山尖约高8.1米。街道机位与相机参数均有误差，绝对尺寸约有0.25至0.45米不确定性。临街砖墙西端两樘窗用作比例基准。偏东的窗在独立街景交会与同平面照片解算之间有约0.8至1.3米的轴位差，第五樘只有一个街景测向。当前立面保留照片上的开口关系。[跨机位核对](measurements/western-bay-and-brick-window-survey.json)

树干、车辆和设备遮挡了部分窗边与砖芯，重复图案依同墙清楚处补全。[平面配准](measurements/primary-front-control.json) · [逐窗位置](measurements/brick-front-openings.json)

模型从画面可辨的东侧砖墙截面延伸到西端浅券门和凸窗。后排坡顶的产权边界、内部和东侧街面延续部分待核。运行 `python measurements/check_mesh.py output` 可生成近远两档网格和封闭性报告，再以 `python measurements/render_front.py output/full-source.glb output/views` 生成原相机视图。[材质源码](source/brick_finishes.py)
