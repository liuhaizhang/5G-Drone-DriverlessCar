import os
import cv2
import multiprocessing as mp
# subprocess 模块允许我们启动一个新进程，并连接到它们的输入/输出/错误管道，从而获取返回值。
import subprocess
import time
from util.need import public_write_log #常规写日志
import sys
from util.need import TIME_FORMAT #字符串时间格式
from util.need import make_pid_file #创建pid文件，保存pid文件
import threading


#从摄像头中获取到一帧一帧的画面
def put_img(queue, maxsize):
    print(os.getpid(), 'put_img')
    '''
    :param queue:  公共的队列，用来存要推流的图片
    :param maxsize:  公共队列的最大值
    :return:
    '''
    '''1、将图片处理进程的pid记录到pid文件中'''
    threading.Thread(target=make_pid_file(os.path.basename(__file__).split('.')[0]+'.txt',os.getpid(),'image')).start()

    '''2、获取摄像头的数据，这个没有部分使用多线程'''
    # 视频读取对象
    cap = cv2.VideoCapture(1)
    cap.set(3,1280) #设置摄像头宽度
    cap.set(4,720) #设置摄像头高度
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))) #构建宽度和高度的元组
    while cap.isOpened():
        # 读取一帧
        ret, frame = cap.read()
        if frame is None:
            print('read frame error!')
            continue
        '''将画面显示出来'''
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        cv2.imshow("nobodycar", frame)

        # 按键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # 读取尺寸、推流
        img = cv2.resize(frame, size)
        if queue.qsize() > maxsize - 1:
            # 当队列差一个就到最大限制数量时，先丢弃一个再放入
            queue.get()
        queue.put(img.tobytes())
    # # 关闭窗口
    cv2.destroyAllWindows()
    # # 停止读取
    cap.release()

#把摄像头获取到的一帧一帧的画面推送
def push_frame(queue, remote_url):
    # 推流地址
    # 推流的服务器地址

    # 设置推流的参数
    command = ['ffmpeg',
               #全局参数
               '-y',
               '-f', 'rawvideo',
               '-vcodec', 'rawvideo',
               '-pix_fmt', 'bgr24',

               '-s', '1280*720',  # 根据输入视频尺寸填写，要和put_img中设置的宽度和高度一样，不然拿到的画面会跳到
               '-r', '25',
               '-i', '-',  #视频输入是从pipe:0 中来

               #视频参数
               '-rtbufsize', '10M',#实时缓存区，需要将流家族到缓冲区，才能操作的
               '-c:v', 'h264',
               '-pix_fmt', 'yuv420p',
               '-force_key_frames', 'expr:gte(t,n_forced*0.5)',  # 加上这个参数，缩短关键帧时间，减少拉流时间
               '-preset', 'ultrafast',
               '-tune', 'zerolatency',  # 低时延编码，加上后延迟再300毫秒左右，但画质会差一些，建议加上
               # '-sc_threshold', '500',#加上后，延迟在300左右，但画面会卡顿，建议不加
               # '-flvflags', 'no_duration_filesize', #加上后延迟跑到500以上，建议不加
               '-f', 'flv',
               remote_url
               ]

    child = subprocess.Popen(command, stdin=subprocess.PIPE)
    print(child.pid,'ffmpeg进程的id','push的进程id',os.getpid())
    '''1、将推流进程的pid记录到pid文件中'''
    threading.Thread(target=make_pid_file(os.path.basename(__file__).split('.')[0]+'.txt',child.pid,'push')).start()

    def inner(child, queue):
        '''往subprocess的文本缓存队列中存储数据，这个可以使用多线程'''
        while True:
            # 从队列中拿到图片进行推流
            try:
                ret = queue.get()
                if ret:
                    #把图片放到subprocess的pipe中
                    child.stdin.write(ret)
            except Exception as e:
                child.kill() #报错后，杀掉ffmpeg的进程
                print(f'推流报错：{e}')
                public_write_log(f'nobodaycar\{TIME_FORMAT}.log',f'{e}\nfilename={__file__}\nfunction={sys._getframe().f_code.co_name}',format='%(message)s') #2023-03-28，屏幕报错的日志
                return False
    #将图片放到ffmpeg中进行推流
    inner(child,queue)
    #等待推流结束
    child.wait()
    return False

# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    '''
    功能：将无人车的画面，推流到srs服务器，签到再从srs服务器上获取数据，播放画面
    推流地址： rtmp://域名:端口/app/stream?token=xxxx
    1、rtmp，走rtmp的协议
    2、端口：是srs中配置rtmp的端口，默认使用的是1935 ，如果srs中配置的rtmp端口变化，这里就需要变化
    3、流地址：app 代表的一种应用的流的前缀，我们设置为急救车的编号，car-0001(当前急救车在数据库中设置的编号) 
    4、stream：是具体流地址, car-0001-nobodycar 具体流地址的设置：急救车编号-从哪里获取的流，screen是救护仪屏幕
    '''
    from util.need import check_ambulance_status #检查急救车是否有任务
    from util.need import encode_token#token认证
    from util.need import CAR_NUMBER#急救车编号
    from util.need import REMOTE_IP#服务器域名
    # CAR_NUMBER 急救车编号
    # REMOTE_IP 服务器域名
    # 流地址
    '''0、将主进程的pid记录到pid文件中'''
    threading.Thread(target=make_pid_file(os.path.basename(__file__).split('.')[0]+'.txt',os.getpid(),'main')).start()
    print('main 的pid',os.getpid())

    STREAM = f'{CAR_NUMBER}-nobodycar'
    '''1、开机时，先等待3秒，再推流操作'''
    print('开机等待3秒，等待电脑运行正常...')
    time.sleep(3)  #正式环境时，再开启


    '''2、推流前，需要先确定当前急救车是否有任务，如果没有就休眠1分钟再请求,拿到急救任务的编号'''
    CHECK_URL = 'https://ambulance.thearay.net/api/srs/ambulance-before-send'
    data = check_ambulance_status(CHECK_URL,CAR_NUMBER) #得等待固定IP可以使用了，才能使用，不然http请求打不过去
    # 视频协议使用的端口
    PROTOCOL_PORT = data.get('stream_port')
    print(data)

    '''3、获取屏幕数据，推送数据,从获取数据到推送（17秒）'''
    token = encode_token(key=CAR_NUMBER) #生成急救车的token
    maxsize = 4  #存放画面的队列
    queue = mp.Queue(maxsize=maxsize)
    remote_url = f"rtmp://{REMOTE_IP}:{PROTOCOL_PORT.get('rtmp')}/{CAR_NUMBER}/{STREAM}?token={token}" #远端地址
    put = mp.Process(target=put_img, args=(queue, maxsize)) #获取屏幕画面放到队列中
    put.start()
    co = 1
    while True:
        # push = mp.Process(target=push_frame, args=(queue, remote_url))
        # push.start()
        # push.join() #等待ffmpeg进程推流结束，循环执行推流命令
        push_frame(queue,remote_url)
        print(f'推流失败 {co}次：等待5秒...')
        time.sleep(5)
        co+=1
