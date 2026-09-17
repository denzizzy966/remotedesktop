import io
import time
import base64
import platform
from PIL import Image, ImageDraw, ImageFont

# Try importing mss
try:
    from mss import MSS
    MSS_AVAILABLE = True
except Exception:
    MSS_AVAILABLE = False

def switch_to_input_desktop():
    """Attempts to attach current thread to the active input desktop (handles Lock Screen / UAC)."""
    if platform.system() == "Windows":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # 0x01FF = MAXIMUM_ALLOWED
            hDesk = user32.OpenInputDesktop(0, False, 0x01FF)
            if hDesk:
                user32.SetThreadDesktop(hDesk)
                user32.CloseDesktop(hDesk)
                return True
        except Exception:
            pass
    return False

def grab_gdi_frame():
    """Direct GDI BitBlt capture, capable of capturing the active input desktop when elevated."""
    if platform.system() != "Windows":
        return None
    try:
        import ctypes
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        switch_to_input_desktop()

        w = user32.GetSystemMetrics(0) # SM_CXSCREEN
        h = user32.GetSystemMetrics(1) # SM_CYSCREEN
        if w <= 0 or h <= 0:
            return None

        hDesktopWnd = user32.GetDesktopWindow()
        hDesktopDC = user32.GetDC(hDesktopWnd)
        if not hDesktopDC:
            return None

        hCaptureDC = gdi32.CreateCompatibleDC(hDesktopDC)
        hCaptureBitmap = gdi32.CreateCompatibleBitmap(hDesktopDC, w, h)
        hOld = gdi32.SelectObject(hCaptureDC, hCaptureBitmap)

        # 0x00CC0020 = SRCCOPY, 0x40000000 = CAPTUREBLT
        gdi32.BitBlt(hCaptureDC, 0, 0, w, h, hDesktopDC, 0, 0, 0x00CC0020 | 0x40000000)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', ctypes.c_uint32),
                ('biWidth', ctypes.c_int32),
                ('biHeight', ctypes.c_int32),
                ('biPlanes', ctypes.c_uint16),
                ('biBitCount', ctypes.c_uint16),
                ('biCompression', ctypes.c_uint32),
                ('biSizeImage', ctypes.c_uint32),
                ('biXPelsPerMeter', ctypes.c_int32),
                ('biYPelsPerMeter', ctypes.c_int32),
                ('biClrUsed', ctypes.c_uint32),
                ('biClrImportant', ctypes.c_uint32)
            ]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h # top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0

        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(hCaptureDC, hCaptureBitmap, 0, h, buf, ctypes.byref(bmi), 0)
        img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')

        gdi32.SelectObject(hCaptureDC, hOld)
        gdi32.DeleteObject(hCaptureBitmap)
        gdi32.DeleteDC(hCaptureDC)
        user32.ReleaseDC(hDesktopWnd, hDesktopDC)
        return img
    except Exception:
        return None

class ScreenCapture:
    def __init__(self):
        self.sct = None
        self.last_error = None
        self.monitor_index = 1 # 1 is primary monitor in mss
        self.init_mss()

    def init_mss(self):
        if MSS_AVAILABLE:
            try:
                self.sct = MSS()
            except Exception as e:
                self.last_error = str(e)
                self.sct = None

    def get_monitors(self):
        """Returns list of available monitors."""
        monitors = []
        if self.sct:
            try:
                for idx, m in enumerate(self.sct.monitors):
                    if idx == 0:
                        continue # index 0 is "all monitors combined"
                    monitors.append({
                        "index": idx,
                        "name": f"Monitor {idx}",
                        "width": m["width"],
                        "height": m["height"],
                        "left": m["left"],
                        "top": m["top"]
                    })
            except Exception:
                pass
        
        if not monitors:
            # Fallback default
            monitors.append({
                "index": 1,
                "name": "Primary Display",
                "width": 1920,
                "height": 1080,
                "left": 0,
                "top": 0
            })
        return monitors

    def capture_frame(self, scale=0.75, quality=60, monitor_index=1):
        """
        Captures the screen and returns a JPEG byte stream along with width and height.
        Falls back to GDI or generating an informative status placeholder if screen is locked.
        """
        raw_img = None
        
        # 0. Windows: ensure thread is on current active desktop (e.g. Winlogon/Lock Screen)
        if platform.system() == "Windows":
            switch_to_input_desktop()

        # 1. Attempt MSS capture
        if not self.sct:
            self.init_mss()

        if self.sct:
            try:
                monitors = self.sct.monitors
                target_mon = monitors[monitor_index] if monitor_index < len(monitors) else monitors[1]
                sct_img = self.sct.grab(target_mon)
                # Convert raw BGRA to PIL Image RGB
                raw_img = Image.frombytes("RGB", (sct_img.width, sct_img.height), sct_img.rgb)
            except Exception as e:
                self.last_error = str(e)
                # Re-initialize mss on failure
                try:
                    self.sct.close()
                except Exception:
                    pass
                self.sct = None

        # 2. Fallback to direct GDI BitBlt on Windows
        if raw_img is None and platform.system() == "Windows":
            raw_img = grab_gdi_frame()

        # 3. Fallback to PIL ImageGrab if MSS & GDI failed
        if raw_img is None:
            try:
                from PIL import ImageGrab
                raw_img = ImageGrab.grab()
            except Exception as e:
                self.last_error = str(e)

        # 4. Fallback placeholder if screen is locked and process lacks elevated desktop permission
        if raw_img is None:
            raw_img = self._create_locked_placeholder()

        orig_w, orig_h = raw_img.size

        # Apply scaling if requested
        if scale != 1.0 and scale > 0.1:
            new_w = max(100, int(orig_w * scale))
            new_h = max(100, int(orig_h * scale))
            img_to_encode = raw_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        else:
            img_to_encode = raw_img

        # Compress to JPEG
        buf = io.BytesIO()
        img_to_encode.save(buf, format="JPEG", quality=quality, optimize=True)
        jpeg_bytes = buf.getvalue()

        return {
            "bytes": jpeg_bytes,
            "width": orig_w,
            "height": orig_h,
            "rendered_width": img_to_encode.width,
            "rendered_height": img_to_encode.height
        }

    def capture_thumbnail(self, max_width=320, max_height=180, quality=50):
        """Generates a compact base64 JPEG thumbnail for the dashboard card."""
        try:
            frame = self.capture_frame(scale=0.25, quality=quality)
            img = Image.open(io.BytesIO(frame["bytes"]))
            img.thumbnail((max_width, max_height))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception:
            # Fallback blank base64 thumbnail
            return ""

    def _create_locked_placeholder(self):
        """Creates an informative screen image when the desktop is locked or display is asleep."""
        w, h = 1280, 720
        img = Image.new("RGB", (w, h), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        
        # Draw background container
        draw.rectangle([w//4 - 50, h//4 - 20, 3*w//4 + 50, 3*h//4 + 20], fill=(30, 41, 59), outline=(99, 102, 241), width=2)
        
        msg1 = "[ WINDOWS DESKTOP LOCKED / SLEEPING ]"
        msg2 = "Layar PC client sedang dikunci (Secure Desktop / Winlogon) atau Sleep."
        msg3 = "Mekanisme keamanan Windows UIPI membatasi capture non-Administrator."
        msg4 = "Solusi: Jalankan client via Task Scheduler / Administrator untuk membuka akses penuh."
        msg5 = "Gunakan tombol 'Wake Screen' di atas untuk menyalakan monitor remote."
        
        # Simple text drawing
        draw.text((w//2 - 190, h//2 - 80), msg1, fill=(248, 113, 113))
        draw.text((w//2 - 250, h//2 - 30), msg2, fill=(243, 244, 246))
        draw.text((w//2 - 270, h//2 + 5), msg3, fill=(156, 163, 175))
        draw.text((w//2 - 300, h//2 + 40), msg4, fill=(96, 165, 250))
        draw.text((w//2 - 220, h//2 + 75), msg5, fill=(52, 211, 153))
        
        return img

    def close(self):
        if self.sct:
            try:
                self.sct.close()
            except Exception:
                pass
            self.sct = None
