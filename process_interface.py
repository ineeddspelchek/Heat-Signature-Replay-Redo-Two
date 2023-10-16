# unused code was commented out by me (ineeddspelechek) not the original author
# try, excepts also added by me

import psutil
from ctypes import *
from ctypes.wintypes import BOOL
import win32con  # from pywin32


def get_pid(process_name):
    for process in psutil.process_iter():
        if process_name in process.name():
            return process.pid
    return None


class ProcessInterface(object):
    def __init__(self):
        self.h_process = None
        self.pid = None

    def open(self, name):
        pid = get_pid(name)
        if pid is None:
            raise RuntimeError(f'Could not find a process name containing "{name}"')
        self.pid = pid
        self._get_handle(self.pid)

    def close(self, code=0):
        windll.kernel32.TerminateProcess(self.h_process, code)
        windll.kernel32.CloseHandle(self.h_process)

    def _get_handle(self, pid):
        self.h_process = windll.kernel32.OpenProcess(
            win32con.PROCESS_VM_READ | win32con.PROCESS_VM_WRITE | win32con.PROCESS_ALL_ACCESS | win32con.DEBUG_PROCESS,
            False, pid)
        if self.h_process:
            print(end="") # print("Success: Got Handle - PID:", self.pid)
        else:
            print("Failed: Get Handle - Error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)

    def read_memory(self, address, buffer_size=4):
        #modified from original author's code
        through = False
        while(not through):
            try:
                buf = create_string_buffer(buffer_size)
                through = True
            except KeyboardInterrupt:
                pass
        #####################################
        
        bytes_read = c_ulong(0)
        if windll.kernel32.ReadProcessMemory(self.h_process, address, buf, buffer_size, byref(bytes_read)):
            return buf
        else:
            print("Failed: Read Memory - Error Code: ", windll.kernel32.GetLastError())
            windll.kernel32.CloseHandle(self.h_process)
            windll.kernel32.SetLastError(10000)

    # def write_memory(self, address, data, length=4):
    #     count = c_ulong(0)

    #     c_int(0)
    #     if not windll.kernel32.WriteProcessMemory(self.h_process, address, byref(data), length, byref(count)):
    #         print("Failed: Write Memory - Error Code: ", FormatError(windll.kernel32.GetLastError()))
    #         windll.kernel32.SetLastError(10000)
    #     else:
    #         return False