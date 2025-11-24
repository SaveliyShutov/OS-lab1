import os
import platform
import getpass
import socket
import multiprocessing

def read_meminfo():
    # Читает /proc/meminfo и возвращает словарь с параметрами памяти
    meminfo = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            key, value = line.split(":")
            meminfo[key] = int(value.strip().split()[0])  # в kB
    return meminfo

def get_os_name():
    # Возвращает название и версию Linux из /etc/os-release
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            data = {}
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k] = v.strip('"')
        return f"{data.get('NAME', '')} {data.get('VERSION', '')}"
    return "Unknown Linux"

def list_drives():
    # Собирает список подключённых дисков и их свободное/общее место
    drives = []
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            device, mountpoint, fstype = parts[0], parts[1], parts[2]

            if not device.startswith("/dev/"):
                continue

            try:
                stat = os.statvfs(mountpoint)
                total = (stat.f_blocks * stat.f_frsize) / (1024 * 1024 * 1024)
                free = (stat.f_bfree * stat.f_frsize) / (1024 * 1024 * 1024)
                drives.append((mountpoint, fstype, free, total))
            except:
                continue
    return drives

def main():
    uname = platform.uname()
    os_name = get_os_name()
    meminfo = read_meminfo()

    total_ram = meminfo.get("MemTotal", 0) // 1024
    free_ram = meminfo.get("MemAvailable", 0) // 1024

    total_swap = meminfo.get("SwapTotal", 0) // 1024
    free_swap = meminfo.get("SwapFree", 0) // 1024

    virtual_mem = meminfo.get("VmallocTotal", 0) // 1024

    load1, load5, load15 = os.getloadavg()
    cpu_count = multiprocessing.cpu_count()

    hostname = socket.gethostname()
    user = getpass.getuser()

    print(f"OS: {os_name}")
    print(f"Kernel: {uname.system} {uname.release}")
    print(f"Architecture: {uname.machine}")
    print(f"Hostname: {hostname}")
    print(f"User: {user}")

    print(f"RAM: {free_ram}MB free / {total_ram}MB total")
    print(f"Swap: {total_swap}MB total / {free_swap}MB free")

    if virtual_mem > 0:
        print(f"Virtual memory: {virtual_mem}MB")
    else:
        print("Virtual memory: unknown")

    print(f"Processors: {cpu_count}")
    print(f"Load average: {load1:.2f}, {load5:.2f}, {load15:.2f}")

    print("Drives:")
    for mp, fs, free, total in list_drives():
        print(f"  {mp:<10} {fs:<6} {free:.1f}GB free / {total:.1f}GB total")

if __name__ == "__main__":
    main()
