import os
import ctypes
from ctypes import wintypes

def get_windows_version():
    """Возвращает версию Windows"""
    # Формат структуры для RtlGetVersion
    class OSVERSIONINFOEXW(ctypes.Structure):
        _fields_ = [
            ("dwOSVersionInfoSize", wintypes.DWORD),
            ("dwMajorVersion", wintypes.DWORD),
            ("dwMinorVersion", wintypes.DWORD),
            ("dwBuildNumber", wintypes.DWORD),
            ("dwPlatformId", wintypes.DWORD),
            ("szCSDVersion", wintypes.WCHAR * 128),
            ("wServicePackMajor", wintypes.WORD),
            ("wServicePackMinor", wintypes.WORD),
            ("wSuiteMask", wintypes.WORD),
            ("wProductType", wintypes.BYTE),
            ("wReserved", wintypes.BYTE),
        ]
    
    try:
        RtlGetVersion = ctypes.windll.ntdll.RtlGetVersion  # системная функция получения версии
        RtlGetVersion.argtypes = [ctypes.POINTER(OSVERSIONINFOEXW)]
        RtlGetVersion.restype = ctypes.c_long
        
        info = OSVERSIONINFOEXW()
        info.dwOSVersionInfoSize = ctypes.sizeof(info)
        
        result = RtlGetVersion(ctypes.byref(info))
        if result != 0:
            return "Unknown Windows Version"
        
        # Формируем человекочитаемую строку версии
        return f"Windows {info.dwMajorVersion}.{info.dwMinorVersion} (Build {info.dwBuildNumber})"
    except Exception as e:
        return f"Error retrieving Windows version: {str(e)}"

def get_computer_user_names():
    """Возвращает имя компьютера и пользователя"""
    # Берём имя компьютера из окружения
    computer = os.environ.get("COMPUTERNAME", "Unknown")
    try:
        user = os.getlogin()  # пытаемся получить логин текущего пользователя
    except Exception:
        user = os.environ.get("USERNAME", "Unknown")  # fallback на переменную окружения
    return computer, user

def get_system_info():
    """Возвращает количество процессоров и архитектуру"""
    # Описание структуры SYSTEM_INFO для GetSystemInfo
    class SYSTEM_INFO(ctypes.Structure):
        _fields_ = [
            ("wProcessorArchitecture", wintypes.WORD),
            ("wReserved", wintypes.WORD),
            ("dwPageSize", wintypes.DWORD),
            ("lpMinimumApplicationAddress", wintypes.LPVOID),
            ("lpMaximumApplicationAddress", wintypes.LPVOID),
            ("dwActiveProcessorMask", ctypes.POINTER(wintypes.DWORD)),
            ("dwNumberOfProcessors", wintypes.DWORD),
            ("dwProcessorType", wintypes.DWORD),
            ("dwAllocationGranularity", wintypes.DWORD),
            ("wProcessorLevel", wintypes.WORD),
            ("wProcessorRevision", wintypes.WORD),
        ]
    
    info = SYSTEM_INFO()
    ctypes.windll.kernel32.GetSystemInfo(ctypes.byref(info))  # вызываем WinAPI
    
    arch_map = {
        0: "x86",
        9: "x64 (AMD64)",
        5: "ARM",
        12: "ARM64"
    }
    # Переводим код архитектуры в строку
    arch = arch_map.get(info.wProcessorArchitecture, f"Unknown ({info.wProcessorArchitecture})")
    
    return info.dwNumberOfProcessors, arch

def get_memory_info():
    """Возвращает RAM, виртуальную память и загрузку памяти"""
    # Описание структуры MEMORYSTATUSEX для GlobalMemoryStatusEx
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    
    mem = MEMORYSTATUSEX()
    mem.dwLength = ctypes.sizeof(mem)
    
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
        raise RuntimeError("Failed to get memory status")  # при ошибке выбрасываем исключение
    
    # Перевод значений в мегабайты
    total_ram = mem.ullTotalPhys // (1024 * 1024)
    avail_ram = mem.ullAvailPhys // (1024 * 1024)
    mem_load = mem.dwMemoryLoad
    total_virtual = mem.ullTotalVirtual // (1024 * 1024)
    
    return avail_ram, total_ram, mem_load, total_virtual

def get_pagefile_info():
    """Возвращает использование файла подкачки"""
    # Описание структуры PERFORMANCE_INFORMATION для GetPerformanceInfo
    class PERFORMANCE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("CommitTotal", ctypes.c_size_t),
            ("CommitLimit", ctypes.c_size_t),
            ("CommitPeak", ctypes.c_size_t),
            ("PhysicalTotal", ctypes.c_size_t),
            ("PhysicalAvailable", ctypes.c_size_t),
            ("SystemCache", ctypes.c_size_t),
            ("KernelTotal", ctypes.c_size_t),
            ("KernelPaged", ctypes.c_size_t),
            ("KernelNonpaged", ctypes.c_size_t),
            ("PageSize", ctypes.c_size_t),
            ("HandleCount", wintypes.DWORD),
            ("ProcessCount", wintypes.DWORD),
            ("ThreadCount", wintypes.DWORD),
        ]
    
    perf = PERFORMANCE_INFORMATION()
    perf.cb = ctypes.sizeof(perf)
    
    if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(perf), perf.cb):
        raise RuntimeError("Failed to get performance info")  # ошибка при вызове API
    
    # Перевод из страниц в мегабайты
    total = (perf.CommitLimit * perf.PageSize) // (1024 * 1024)
    used = (perf.CommitTotal * perf.PageSize) // (1024 * 1024)
    
    return used, total

def get_drives_info():
    """Возвращает список логических дисков с их объёмом и свободным местом"""
    drives_list = []
    buf = ctypes.create_unicode_buffer(1024)  # буфер для списка дисков
    
    if ctypes.windll.kernel32.GetLogicalDriveStringsW(ctypes.sizeof(buf) // 2, buf):
        drives = buf.value.split('\x00')  # разделяем нулевыми символами
        for drive in drives:
            if drive.strip():
                try:
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    free_for_user = ctypes.c_ulonglong(0)
                    
                    if ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        drive, 
                        ctypes.byref(free_for_user), 
                        ctypes.byref(total_bytes), 
                        ctypes.byref(free_bytes)
                    ):
                        # перевод байт в гигабайты
                        total_gb = total_bytes.value / (1024 * 1024 * 1024)
                        free_gb = free_bytes.value / (1024 * 1024 * 1024)
                        used_gb = total_gb - free_gb
                        usage_percent = (used_gb / total_gb) * 100 if total_gb > 0 else 0
                        
                        # Формируем строку с информацией о диске
                        drives_list.append(
                            f"{drive} - {used_gb:.1f}GB / {total_gb:.1f}GB "
                            f"({free_gb:.1f}GB free, {usage_percent:.1f}% used)"
                        )
                    else:
                        drives_list.append(f"{drive} - error reading disk")
                except Exception as e:
                    drives_list.append(f"{drive} - error: {str(e)}")
    
    return drives_list

def format_bytes(size_bytes):
    """Форматирует байты в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"  # выбираем подходящую единицу
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def main():
    print("=" * 50)
    print("SYSTEM INFORMATION")
    print("=" * 50)
    
    print(f"OS: {get_windows_version()}")  # вывод версии Windows
    
    computer, user = get_computer_user_names()
    print(f"Computer Name: {computer}")  # имя компьютера
    print(f"User: {user}")  # имя пользователя
    
    processors, arch = get_system_info()
    print(f"Architecture: {arch}")  # архитектура CPU
    print(f"Processors: {processors}")  # количество процессоров
    
    try:
        avail_ram, total_ram, mem_load, total_virtual = get_memory_info()
        used_ram = total_ram - avail_ram
        print(f"RAM: {used_ram}MB / {total_ram}MB ({mem_load}% used)")  # использование RAM
        print(f"Available RAM: {avail_ram}MB")
        print(f"Virtual Memory: {total_virtual}MB")
    except Exception as e:
        print(f"Memory info error: {e}")
    
    try:
        pagefile_used, pagefile_total = get_pagefile_info()
        print(f"Pagefile: {pagefile_used}MB / {pagefile_total}MB")  # информация о подкачке
    except Exception as e:
        print(f"Pagefile info error: {e}")
    
    print("\nDrives:")  # список логических дисков
    for drive in get_drives_info():
        print(f"  - {drive}")

if name == "__main__":
    main()
