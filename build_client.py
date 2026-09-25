import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(BASE_DIR, "client")

def build_client():
    print("=" * 65)
    print(" Building Standalone LANRemoteClient.exe (Offline Single Executable)...")
    print("=" * 65)

    client_entry = os.path.join(CLIENT_DIR, "client.py")
    dist_dir = os.path.join(BASE_DIR, "dist")
    build_dir = os.path.join(BASE_DIR, "build")

    # Command arguments for PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--name", "LANRemoteClient",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        "--paths", CLIENT_DIR,
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "websockets.legacy",
        "--hidden-import", "websockets.legacy.client",
        "--hidden-import", "mss",
        "--hidden-import", "psutil",
        "--hidden-import", "PIL",
        "--hidden-import", "pyautogui",
        "--hidden-import", "pyperclip",
        "--hidden-import", "pystray",
        "--hidden-import", "pystray._win32",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "settings_ui",
        client_entry
    ]

    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=BASE_DIR)
    
    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "LANRemoteClient.exe")
        client_exe_path = os.path.join(CLIENT_DIR, "LANRemoteClient.exe")
        try:
            shutil.copy2(exe_path, client_exe_path)
            print(f"[Copied] Automatically synced to {client_exe_path}")
        except Exception as e:
            print(f"[Warning] Failed to copy to client dir: {e}")

        print("=" * 65)
        print("[SUCCESS] Build Completed!")
        print(f"Standalone Executable: {exe_path}")
        if os.path.exists(exe_path):
            size_mb = round(os.path.getsize(exe_path) / (1024 * 1024), 2)
            print(f"File Size: {size_mb} MB")
        print("Anda cukup meng-copy file 'LANRemoteClient.exe' ini ke PC target!")
        print("PC target TIDAK MEMERLUKAN Python, pip, maupun koneksi internet.")
        print("=" * 65)
        return True
    else:
        print("[ERROR] PyInstaller build failed.")
        return False

if __name__ == "__main__":
    build_client()
