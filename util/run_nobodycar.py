import time
from need import NOBODY_CAR_URL_WS, CAR_NUMBER,BASE_DIR,check_nobodycar_status_ws
import os
import subprocess
import json

#推流脚本的路径
NOBODYCAR_PATH = os.path.join(BASE_DIR,'nobodycar.py',)


#2023-04-14推流杀掉进程，再重新开始
def restart_nobodycar():
    '''
    设置开机自启动，用来控制无人车视频重新推流的操作
    '''
    '''0、开机时，先运行 根目录下的nobodycar.py 模块'''
    subprocess.Popen(['python', f'{NOBODYCAR_PATH}'], shell=False)

    '''下面是结束推流进程，进入下一个推流循环'''
    while True:
        '''
        1、开机时是，nobodycar 和 need下的 restart_nobodycar 启动
        2、中止一次后，就是循环 restart_nobodycar
        '''

        '1、请求后端，判断是否开始推送无人车视频，开始了才可以结束'
        check_nobodycar_status_ws(NOBODY_CAR_URL_WS, CAR_NUMBER)

        '2、请求后端，判断是否结束无人车操作或任务结束'
        check_nobodycar_status_ws(NOBODY_CAR_URL_WS,CAR_NUMBER,the_type='end')

        '3、结束推流无人车视频'
        path = os.path.join(BASE_DIR,'pid_file','nobodycar.txt')
        if not os.path.exists(path):
            while True:
                if os.path.exists(path):
                    break
                time.sleep(5)

        with open(path,'r') as fp:
            dic = fp.read()
        os.remove(path)
        try:
            dic = json.loads(dic)
            push_pid = dic.get('push')
            image_pid = dic.get('image')
            main_pid = dic.get('main')

            push = subprocess.Popen(['taskkill', '-f', '-pid', f'{push_pid}'], shell=False)
            image = subprocess.Popen(['taskkill', '-f', '-pid', f'{image_pid}'], shell=False)
            main = subprocess.Popen(['taskkill', '-f', '-pid', f'{main_pid}'], shell=False)
            print(f'push返回值={push.returncode}, 杀掉推流的进程')
            print(f'main返回值 = {main.returncode},杀掉播放的主进程')
            print(f'play返回值 = {image.returncode}，杀掉播放的子进程')
        except Exception as e:
            pass
        '4、重新执行推流无人车视频（进入新的循环）'
        subprocess.Popen(['python',f'{os.path.join(BASE_DIR, "nobodycar.py")}'], stdin=subprocess.PIPE, shell=True)

if __name__ == '__main__':
    restart_nobodycar()