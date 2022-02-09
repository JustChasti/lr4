from multiprocessing import Process
import threading
import numpy as np
from winsys import ipc
import win32pipe, win32file, pywintypes
from time import sleep


def multi1():
    # подключаемся к ящику
    with ipc.mailslot("first") as l:
        while True:
            word = l.get()  # получаем сообщение
            if '*' in word:
                data = 1
                for i in word.split('*'):
                    data *= float(i)
                name = r"\\*\mailslot\first-resp"
                mail = ipc.mailslot(name)  # отправляем ответ в еще один ящик
                mail.put(data)
                break
            else:
                print(word)


def multi2():
    print("pipe client")
    quit = False
    while not quit:
        try:
            # подключение к каналу
            handle = win32file.CreateFile(
                r'\\.\pipe\Foo',
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
            if res == 0:
                print(f"SetNamedPipeHandleState return code: {res}")
            while True:
                # получаем инфу из канала
                resp = win32file.ReadFile(handle, 64*1024)
                res = str(resp).split("'")[1].split('*')
                result = 1
                for i in res:
                    result *= float(i)
                # создаем другой канал и пишем туда инфу и получаем так же обратно в основном потоке
                name = r'\\.\pipe\Foo1'
                pipe = win32pipe.CreateNamedPipe(
                    name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    1, 65536, 65536,
                    0,
                    None
                )
                flag = False
                while True:
                    try:
                        print("try return information")
                        win32pipe.ConnectNamedPipe(pipe, None)
                        some_data = str.encode(f"{result}")
                        win32file.WriteFile(pipe, some_data)
                        sleep(1)
                        win32file.CloseHandle(pipe)
                        flag = True
                        break
                    except Exception as e:
                        print(e)
                        sleep(0.1)
                if flag:
                    quit = True
                    break
        except pywintypes.error as e:
            print(e, '1 часть')
            sleep(0.1)


def worker(data):
    threading.Thread(target=multi1).start()
    name = r"\\*\mailslot\first"
    mail = ipc.mailslot(name)
    mail.put(data)
    print('finish 1')
    name = "first-resp"
    d = 0
    with ipc.mailslot(name) as l:
        while True:
            word = l.get()
            sw = str(word)
            if '.' in sw:
                d += float(word)
                break
    return d


if __name__ == "__main__":
    matrix = np.array([
        [1, 3, 4],
        [0, 2, 1],
        [1, 5, -1]
    ])
    # вот матрица для примера
    threading.Thread(target=multi1).start()
    name = r"\\*\mailslot\first"
    mail = ipc.mailslot(name)  # отправляем в ящик нужную информацию
    mail.put(f"{matrix[0][0]}*{matrix[1][1]}*{matrix[2][2]}")
    print('finish 1')
    name = "first-resp"
    d = 0
    # читаем данные из ящика
    with ipc.mailslot(name) as l:
        while True:
            word = l.get()
            sw = str(word)
            if '.' in sw:
                d += float(word)
                break
    print(d)

    # создаем канал
    name = r'\\.\pipe\Foo'
    pipe = win32pipe.CreateNamedPipe(
        name,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
        1, 65536, 65536,
        0,
        None
    )
    # запускаем поток 
    threading.Thread(target=multi2).start()
    while True:
        print("waiting for client")
        try:
            print("waiting for client")
            win32pipe.ConnectNamedPipe(pipe, None)  # коннектикмся к каналу
            some_data = str.encode(f"{matrix[2][0]}*{matrix[0][1]}*{matrix[1][2]}")
            win32file.WriteFile(pipe, some_data)  # записываем данные
            sleep(1)
            win32file.CloseHandle(pipe)
            break
        except Exception as e:
            print(e)
            sleep(0.1)

    print("try to get information")
    quit = False
    while not quit:
        try:
            handle = win32file.CreateFile(
                r'\\.\pipe\Foo1',
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
            flag = False
            if res == 0:
                print(f"SetNamedPipeHandleState return code: {res}")
            while True:
                resp = win32file.ReadFile(handle, 64*1024)
                if 'b' in str(resp):
                    dd = float(str(resp).split(',')[1].split("'")[1])
                    print(dd)
                    d += dd
                    flag = True
                    break
            if flag:
                break
        except pywintypes.error as e:
            print(e, '2 часть')
            sleep(0.1)
    dd = worker(f"{matrix[1][0]}*{matrix[2][1]}*{matrix[0][2]}")
    d += dd
    print(dd)
    dd = worker(f"{matrix[2][0]}*{matrix[1][1]}*{matrix[0][2]}")
    d -= dd
    print(dd)
    dd = worker(f"{matrix[1][0]}*{matrix[0][1]}*{matrix[2][2]}")
    d -= dd
    print(dd)
    dd = worker(f"{matrix[0][0]}*{matrix[1][2]}*{matrix[2][1]}")
    d -= dd
    print(dd)
    print('result: ',d)
