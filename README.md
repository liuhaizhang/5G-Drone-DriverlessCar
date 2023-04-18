# 5G_drone_nobodycar
### 一、结构数据

急救车端的推流脚本
需要使用到的结构：

1、logs 目录：存放的是日志文件
2、utils目录：

​	2.1、delete_log.py   用来控制日志保留的数量

​	2.2、log_.py 用来生成日志文件

​	2.3、need.py, 推流脚本公用的方法，token生成，检验当前急救车是否有任务，日志书写

3、drone.py  推送无人机视频到srs服务器上【无人机的画面在平板可以看到，拿的是平板的屏幕画面】

4、nobodycar.py 推送无人车视频到srs服务器上【无人车的画面在遥控器平板可以看到，拿的是平板的屏幕画面】

5、util/run_nobodycar.py  无人车推流的启动文件



需要将无人车和无人机的平板连接到主机上，这些代码机就在这个主机上。





### 二、启动文件：

util/nobodycar.py   : 设置成开机自启动方式

```
2.1、在电脑地址栏输入：C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp
2.2、在该文件夹中创建
	camaro.bat   文件
	
	#文件内容：
	C:
	cd  C:\\data\\project\\5G_drone_nobodycar\\util
	python run_nobodycar.py
```

