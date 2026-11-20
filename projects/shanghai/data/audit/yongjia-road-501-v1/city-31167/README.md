# 主地图实测

在31166的203处地图上，永嘉路501号位置仍显示普通灰色体量。31167增加该住宅后，桌面和390像素手机均能从默认视角看到北面长墙、三只老虎窗以及右侧圆塔的尖顶。街面近图可辨塔脚和窄小西端附间，屋顶近图可辨坡屋及其两侧窗列。近景屋檐下较暗，细小砖饰在俯视和远景中难以辨认。[上一版原图](before/map-before.png) · [桌面默认](after/map-desktop.png) · [手机默认](after/map-mobile.png) · [街面近景](after/map-street-facade.png) · [屋面](after/map-roof.png) · [远景](after/map-distant.png)

后态实际切换近、远两档，204处地图标签数与目录一致。20个地面点包含墙、花园空地和五个邻屋，碰撞结果全部匹配。四件模型文件逐份校核正文，两个实际地图模型与底图远近资源都有浏览器请求记录。两端WebGL均返回零错误，最终关闭浏览器后才记录完成。[前态收据](before/control-browser.json) · [后态收据](after/main-browser.json) · [模型与独立页绑定](standalone-bindings.json)
