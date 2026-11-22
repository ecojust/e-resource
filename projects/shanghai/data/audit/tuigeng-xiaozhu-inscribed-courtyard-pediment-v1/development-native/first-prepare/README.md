# 退耕小筑题额的首次原生工程制作

2026年11月22日，第259期的前态、手机和桌面检查均已退出，桌面已实际保存四份文件。随后题额第一次制作在准备可编辑构件时退出，日志记录了 `TypeError: Unsupported grouped mesh value ndarray`。这一轮只运行了准备程序，未进入 Blender，未产生浏览器截图。[首次进程记录](first-process.json)

弧形压顶的一组坐标由 NumPy 数组保存。准备程序可以写出标量，在把整组坐标写入 JSON 时遇错。修订后的程序将数组按原次序转换为数值列表。两次制作均保存了同一场第259期检查的退出、桌面报告及上一期移交的 SHA-256。[两轮核对记录](two-runs.json)

第二轮成功生成并重开可编辑工程，网页在桌面取得七幅、手机取得四幅，两端共核对四款下载。原生预览可辨右起的「退耕小筑」、连续回纹和弧形压顶。[网页截图与下载](../standalone/viewer.json) · [实际进程](../process/physical-exit.json) · [同场移交](../process/host-return.json)
