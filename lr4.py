from multiprocessing import Process
import threading
import numpy as np
from sqlalchemy import true
from winsys import ipc
import win32pipe, win32file, pywintypes
from time import sleep


def multi1():
    with ipc.mailslot("first") as l:
        while True:
            word = l.get()
            if '*' in word:
                # print(word)
                data = 1
                for i in word.split('*'):
                    data *= float(i)
                name = r"\\*\mailslot\first-resp"
                mail = ipc.mailslot(name)
                mail.put(data)
                break
            else:
                print(word)


def multi2():
    print("pipe client")
    quit = False

    while not quit:
        try:
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
                resp = win32file.ReadFile(handle, 64*1024)
                print(f"message: {resp}")
        except pywintypes.error as e:
            print(e)


if __name__ == "__main__":
    matrix = np.array([
        [1, 0, -2],
        [0.5, 3, 1],
        [0, 2, -1]
    ])
    """
    threading.Thread(target=multi1).start()
    name = r"\\*\mailslot\first"
    mail = ipc.mailslot(name)
    mail.put(f"{matrix[0][0]}*{matrix[1][1]}*{matrix[2][2]}")
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
    print(d)
    """
    name = r'\\.\pipe\Foo'
    pipe = win32pipe.CreateNamedPipe(
        name,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
        1, 65536, 65536,
        0,
        None
    )
    threading.Thread(target=multi2).start()
    while True:
        print("waiting for client")
        try:
            print("waiting for client")
            win32pipe.ConnectNamedPipe(pipe, None)
            some_data = str.encode(f"{matrix[0][1]}*{matrix[1][2]}*{matrix[2][1]}")
            win32file.WriteFile(pipe, some_data)
            sleep(1)
            win32file.CloseHandle(pipe)
            break
        except Exception as e:
            print(e)
            sleep(0.1)
