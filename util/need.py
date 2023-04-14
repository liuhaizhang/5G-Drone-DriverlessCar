import socket
import time
import json
import hmac
import base64
import requests
import subprocess
import os

# 当前急救车编号
CAR_NUMBER = 'car-0001'
# srs服务器的web端
REMOTE_IP = 'ambulance.thearay.net'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#时间格式
TIME_FORMAT = time.strftime('%Y-%m-%d')
TIME_STAMP = time.time()

#获取当前急救车的局域网IP地址【check_ambulance_status使用】
def getip():
    '''获取急救车的局域网IP地址，传递给后端保存起来，平板拉流就直接从局域网拉流'''
    while True:
        try:
             s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
             s.connect(("8.8.8.8", 80))
             ip = s.getsockname()[0]
        except:
            ip = None
        finally:
            s.close()
        if ip:
            return ip
        time.sleep(2)

#急救车端生成的token信息【所有脚本都使用】
def encode_token(key, expire=2*24*60*60):
    r'''
    @Args:
     key: str (用户给定的key，需要用户保存以便之后验证token,每次产生token时的key 都可以是同一个key)
     expire: int(最大有效时间，单位为s)
    @Return:
     state: str
    '''

    live_time = time.time() + expire
    # ts_byte = ts_str.encode("utf-8")
    #把急救车编号放到里面
    dic = {'car_number':key,'time':live_time}
    dic = json.dumps(dic)
    # print(dic,type(dic))
    #急救车编号当盐
    sha1_tshexstr = hmac.new(key.encode("utf-8"), dic.encode('utf-8'), 'sha1').hexdigest()
    token = dic + '#' + sha1_tshexstr
    # print(token)
    b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
    return b64_token.decode("utf-8")

#查看当前急救车是否有急救任务【所有脚本都使用】
def check_ambulance_status(url,car_number):
    '''
    检测当前急救车是否有急救任务的，如果没有就把访问频率降低
    '''
    co = 0
    #获取急救车IP地址
    ip = getip()
    while True:
        #当前急救车的编号
        token = encode_token(key=car_number)#生成token
        headers = {
            'content-type': 'application/json',
            'token': token,
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
        }
        try:
            r = requests.post(url,data=json.dumps({'car_number':car_number,'drone_ip':ip}),headers=headers)
            # print(r.content)
            if r.status_code == 200:
                print('当前急救车有急救任务，可以推送数据',url,time.strftime('%Y-%m-%d %H:%M:%S'))
                data = r.json().get('data') #拿到当前急救车的急救任务编号
                return data
            else:
                #清空队列

                if co<5:
                    #前5次请求，如果急救车没有急救任务，则休眠5秒
                    print('当前急救车没有急救任务,5次请求内，睡眠5秒...')
                    time.sleep(5)

                else:
                    #超过5次，急救车都是没有急救任务的，就休眠1分钟
                    print('当前急救车没有急救任务,超过5次请求，睡眠60秒...')
                    time.sleep(60)
                co+=1

        except Exception as e :
            print('服务器请求超时，睡眠5秒...')
            print('服务器报错=',str(e))
            co+=1
            time.sleep(5)

#测试当前网络是否可用 【给play_audio.py使用，旧的脚本】
def netstatus(queue):
    '''测试当前机器的网络是否可用'''
    while True:
        child = subprocess.run('ping www.baidu.com -n 2', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # print(child.returncode, '返回状态码')
        if child.returncode:
            #连不上网时，队列中放0，代表网络不通
            if queue.empty():
                queue.put(0)
            else:
                queue.get()
                queue.put(0)
        else:
            #能连接上网络时，队列中放1，代表有网络
            if queue.empty():
                queue.put(1)
            else:
                queue.get()
                queue.put(1)

#普通进行直接打日志到文件中
def public_write_log(log_file,content,format = '%(asctime)s: %(message)s'):
    '''
    log_file = nobodaycar/时间.log
    '''
    try:
        from util.log_ import BaseLog
        log = BaseLog(log_file,format=format)
        log.start_log()
        log.set_log(content)
        log.end_log()
    except Exception as e:
        pass

#给推流脚本生成对应的pid文件
def make_pid_file(filename,pid,who):
    '''
    filename: 一个推流脚本，一个pid文件，以nobodycar.py 生成nobodycar.txt 存放pid
    pid：某个进程的pid
    who：指明该pid是那个进程的
    构建成={f'{whow}':f'{pid}'}
    '''
    try:
        path = os.path.join(BASE_DIR,'pid_file',filename)
        if os.path.exists(path):
            #存在文件时，将会修改dic
            with open(path,'r') as fr:
                dic = json.loads(fr.readline())
            dic[who]=pid

            with open(path,'w') as fw:
                fw.write(json.dumps(dic))
        else:
            #pid_file 文件夹不存在时，创建该文件夹
            dir_path = os.path.dirname(path)
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)
            # 不存在时pid文件时，新建一个
            with open(path,'w') as fp:
                fp.write(json.dumps({f'{who}':pid}))
    except Exception as e:
        log_file = filename.split('.')[0] +'/'+time.strftime(TIME_FORMAT)+'.log'
        public_write_log(log_file,f'{e}')




if __name__ == '__main__':
    token = encode_token('car-0001')
    print('token= ',token)
