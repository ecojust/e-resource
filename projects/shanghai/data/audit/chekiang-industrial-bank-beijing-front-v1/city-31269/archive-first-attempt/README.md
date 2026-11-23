第一次归档读取压缩城市清单时，归档程序将读文件函数与场景报告用了同一变量名。处理第二份压缩输入时，Python 抛出 TypeError。当天的十段城市场景和桌面、手机独立页此前都已正常退出。

修正函数名后，归档程序使用原来的场景报告、39 个地面结果、截图和独立页四个实际下载，重新核对并通过。可查[第一次运行日志](post-restart-sequence.log)、[第一次使用的程序](archive-recovered.py)、[修正后的程序](../archive-recovered.py)与[逐项签名](result.json)。
