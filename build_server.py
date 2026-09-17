import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(BASE_DIR, "server")
STATIC_DIR = os.path.join(SERVER_DIR, "static")

def build_server():
    print("=" * 65)
    print(" Building Standalone LANRemoteServer.exe (Offline Admin Server)...")
    print("=" * 65)

    server_entry = os.path.join(BASE_DIR, "run_server.py")
    dist_dir = os.path.join(BASE_DIR, "dist")
    build_dir = os.path.join(BASE_DIR, "build")

    # Command arguments for PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name", "LANRemoteServer",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        "--paths", BASE_DIR,
        "--add-data", f"{STATIC_DIR};server/static",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "fastapi",
        "--hidden-import", "websockets",
        "--hidden-import", "psutil",
        server_entry
    ]

    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=BASE_DIR)
    
    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "LANRemoteServer.exe")
        print("=" * 65)
        print("[SUCCESS] Server Build Completed!")
        print(f"Standalone Executable: {exe_path}")
        print("=" * 65)
        return True
    else:
        print("[ERROR] PyInstaller server build failed.")
        return False

if __name__ == "__main__":
    build_server()
