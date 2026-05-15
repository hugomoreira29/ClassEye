import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import time
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFilter

# ── Colour palette ────────────────────────────────────────────────────────────
BG       = "#080d14"
SURFACE  = "#0f1724"
CARD     = "#141e2e"
CARD2    = "#1a2540"
BORDER   = "#1f2e45"
BORDER2  = "#263550"
ACCENT   = "#2563eb"
ACCENT_H = "#3b82f6"
GREEN    = "#10b981"
GREEN_H  = "#34d399"
RED      = "#ef4444"
YELLOW   = "#f59e0b"
TEXT     = "#f0f4ff"
TEXT_DIM = "#6b7fa3"
TEXT_MID = "#94a3b8"
FONT     = "Segoe UI"

# ── Backend imports ───────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recognition"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "attendance"))

try:
    from recognize_faces import recognize_students
    from encode_faces    import load_known_faces
    BACKEND_OK = True
except ImportError:
    BACKEND_OK = False

try:
    from attendance import mark_attendance
    ATTENDANCE_OK = True
except ImportError:
    ATTENDANCE_OK = False
    def mark_attendance(names, **_): pass

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    import face_recognition
    FR_OK = True
except ImportError:
    FR_OK = False


# ── Utility: rounded rectangle on Canvas ──────────────────────────────────────
def _round_rect(canvas, x1, y1, x2, y2, r=10, **kw):
    canvas.create_arc(x1,     y1,     x1+2*r, y1+2*r, start= 90, extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=  0, extent=90,  style="pieslice", **kw)
    canvas.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90,  style="pieslice", **kw)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, **kw)
    canvas.create_rectangle(x1, y1+r, x2, y2-r, **kw)


# ── Reusable widgets ──────────────────────────────────────────────────────────
class FlatCard(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CARD, bd=0,
                         highlightthickness=1, highlightbackground=BORDER, **kw)


class ModernButton(tk.Frame):
    """A flat button with smooth hover transition."""
    def __init__(self, parent, text, command, bg=ACCENT, fg=TEXT,
                 icon="", width=None, pady=10, **kw):
        super().__init__(parent, bg=parent["bg"], cursor="hand2", **kw)
        self._bg  = bg
        self._hbg = self._lighten(bg)
        self._cmd = command

        inner = tk.Frame(self, bg=bg, pady=pady,
                         padx=14 if not width else 0)
        inner.pack(fill="x")
        if width:
            inner.config(width=width)

        lbl_text = f"{icon}  {text}" if icon else text
        self._lbl = tk.Label(inner, text=lbl_text, bg=bg, fg=fg,
                              font=(FONT, 9, "bold"))
        self._lbl.pack(fill="x")

        for w in (self, inner, self._lbl):
            w.bind("<Enter>",  self._on_enter)
            w.bind("<Leave>",  self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def _on_enter(self, _=None):
        self._set_color(self._hbg)

    def _on_leave(self, _=None):
        self._set_color(self._bg)

    def _on_click(self, _=None):
        if str(self._lbl["state"]) != "disabled":
            self._cmd()

    def _set_color(self, color):
        try:
            for w in self.winfo_children():
                w.config(bg=color)
                for c in w.winfo_children():
                    c.config(bg=color)
        except Exception:
            pass

    def set_state(self, state):
        self._lbl.config(state=state)
        fg = TEXT if state == "normal" else TEXT_DIM
        self._lbl.config(fg=fg)

    @staticmethod
    def _lighten(hex_color):
        try:
            r = min(255, int(hex_color[1:3], 16) + 25)
            g = min(255, int(hex_color[3:5], 16) + 25)
            b = min(255, int(hex_color[5:7], 16) + 25)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color


class StatTile(tk.Frame):
    def __init__(self, parent, label, value="—", color=ACCENT, icon=""):
        super().__init__(parent, bg=CARD2, padx=14, pady=12,
                         highlightthickness=1, highlightbackground=BORDER2)
        top = tk.Frame(self, bg=CARD2)
        top.pack(fill="x")
        tk.Label(top, text=icon, bg=CARD2, fg=color,
                 font=(FONT, 14)).pack(side="left")
        tk.Label(top, text=label, bg=CARD2, fg=TEXT_DIM,
                 font=(FONT, 8)).pack(side="left", padx=(6, 0))
        self._val = tk.Label(self, text=str(value), bg=CARD2, fg=color,
                              font=(FONT, 22, "bold"))
        self._val.pack(anchor="w", pady=(2, 0))

    def set(self, v): self._val.config(text=str(v))


class PulsingDot(tk.Canvas):
    def __init__(self, parent, color=GREEN, size=8, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=parent["bg"], highlightthickness=0, **kw)
        self._color = color
        self._size  = size
        self._step  = 0
        self._animate()

    def _animate(self):
        self.delete("all")
        s = self._size
        t = self._step % 30
        r = (s // 2) * (0.5 + 0.5 * abs(t - 15) / 15)
        c = s // 2
        self.create_oval(c-r, c-r, c+r, c+r, fill=self._color, outline="")
        self._step += 1
        self.after(60, self._animate)


class Separator(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BORDER, height=1, **kw)


# ── Live Camera Window ────────────────────────────────────────────────────────
class CameraWindow(tk.Toplevel):
    DETECT_EVERY = 5
    FPS_INTERVAL = 40

    def __init__(self, parent, on_capture, known_encodings=None, known_names=None,
                 tolerance=0.5, min_frames=3, late_minutes=0):
        super().__init__(parent)
        self.title("ClassEye — Live Camera")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("900x620")

        self._on_capture         = on_capture
        self._known_encodings    = list(known_encodings or [])
        self._known_names        = list(known_names or [])
        self._cap                = None
        self._running            = False
        self._frame_count        = 0
        self._last_locations     = []
        self._last_names         = []
        self._last_confidences   = []
        self._photo              = None
        self._fps_ts             = time.time()
        self._fps_frames         = 0
        self._detecting          = False
        self._current_frame      = None
        self._tolerance          = tolerance
        self._min_frames         = min_frames
        self._late_minutes       = late_minutes
        self._consecutive        = {}
        self._confirmed_present  = set()
        self._late_set           = set()
        self._session_start      = time.time()

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._close)
        threading.Thread(target=self._start_camera, daemon=True).start()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📷", bg=SURFACE, fg=ACCENT,
                 font=(FONT, 16)).pack(side="left", padx=(16, 6), pady=12)
        tk.Label(hdr, text="Live Camera", bg=SURFACE, fg=TEXT,
                 font=(FONT, 13, "bold")).pack(side="left")
        self._fps_lbl = tk.Label(hdr, text="", bg=SURFACE, fg=TEXT_DIM,
                                  font=("Consolas", 8))
        self._fps_lbl.pack(side="right", padx=16)
        self._detect_lbl = tk.Label(hdr, text="Initialising…", bg=SURFACE,
                                     fg=YELLOW, font=(FONT, 9, "bold"))
        self._detect_lbl.pack(side="right", padx=8)

        # Canvas area
        cf = tk.Frame(self, bg=BG)
        cf.pack(fill="both", expand=True, padx=12, pady=8)
        self._canvas = tk.Canvas(cf, bg="#060b12", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        # Bottom bar
        bar = tk.Frame(self, bg=SURFACE, height=60)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self._btn_capture = tk.Button(
            bar, text="📸   Capture & Scan",
            command=self._capture,
            bg=GREEN, fg=BG, font=(FONT, 10, "bold"),
            bd=0, padx=22, pady=8, cursor="hand2",
            activebackground=GREEN_H, activeforeground=BG, relief="flat")
        self._btn_capture.pack(side="left", padx=16, pady=10)

        tk.Button(bar, text="✕  Close", command=self._close,
                  bg=CARD2, fg=TEXT_MID, font=(FONT, 9),
                  bd=0, padx=14, pady=8, cursor="hand2",
                  activebackground=BORDER2, activeforeground=TEXT,
                  relief="flat").pack(side="left", pady=10)

        self._status_lbl = tk.Label(bar, text="Opening camera…",
                                     bg=SURFACE, fg=TEXT_DIM, font=(FONT, 9))
        self._status_lbl.pack(side="right", padx=16)
        tk.Label(bar, text="Position faces · then click Capture",
                 bg=SURFACE, fg=TEXT_DIM, font=(FONT, 8)).pack(side="right", padx=4)

    def _start_camera(self):
        if not CV2_OK:
            self._safe_set(self._status_lbl, text="OpenCV not installed.", fg=RED)
            return
        try:
            cap = cv2.VideoCapture(0)
        except Exception as e:
            self._safe_set(self._status_lbl, text=f"Error: {e}", fg=RED)
            return
        if not cap.isOpened():
            self._safe_set(self._status_lbl, text="Camera not found.", fg=RED)
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap     = cap
        self._running = True
        self._safe_set(self._status_lbl, text="Camera active", fg=GREEN)
        self._safe_set(self._detect_lbl, text="Scanning…",     fg=GREEN)
        try:
            self.after(0, self._loop)
        except Exception:
            pass

    def _loop(self):
        if not self._running:
            return
        try:
            ret, frame = self._cap.read()
            if not ret:
                self.after(self.FPS_INTERVAL, self._loop)
                return
            self._current_frame  = frame
            self._frame_count   += 1
            self._fps_frames    += 1

            if self._frame_count > 1 and \
               self._frame_count % self.DETECT_EVERY == 0 and \
               not self._detecting:
                self._detecting = True
                small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                threading.Thread(target=self._detect,
                                 args=(small,), daemon=True).start()

            display = frame.copy()
            self._draw_boxes(display)
            self._render(display)

            now = time.time()
            if now - self._fps_ts >= 1.0:
                fps = self._fps_frames / (now - self._fps_ts)
                self._fps_frames = 0
                self._fps_ts     = now
                self._safe_set(self._fps_lbl, text=f"{fps:.0f} fps")
            self.after(self.FPS_INTERVAL, self._loop)
        except Exception:
            if self._running:
                self.after(self.FPS_INTERVAL, self._loop)

    def _detect(self, small_bgr):
        try:
            import numpy as np
            rgb  = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
            locs = face_recognition.face_locations(rgb, model="hog")
            locs_full = [(t*2, r*2, b*2, l*2) for t, r, b, l in locs]
            names       = []
            confidences = []
            if self._known_encodings and locs:
                encs = face_recognition.face_encodings(rgb, locs)
                for enc in encs:
                    dists = face_recognition.face_distance(self._known_encodings, enc)
                    if len(dists):
                        idx = np.argmin(dists)
                        if dists[idx] <= self._tolerance:
                            names.append(self._known_names[idx])
                            confidences.append(round((1 - dists[idx]) * 100))
                        else:
                            names.append("Unknown")
                            confidences.append(0)
                    else:
                        names.append("Unknown")
                        confidences.append(0)
            else:
                names       = ["?" for _ in locs]
                confidences = [0] * len(locs)

            # Consecutive frame tracking — only confirm after min_frames detections
            detected_now = set(n for n in names if n not in ("Unknown", "?"))
            for name in list(self._consecutive.keys()):
                if name not in detected_now:
                    self._consecutive[name] = 0
            for name in detected_now:
                self._consecutive[name] = self._consecutive.get(name, 0) + 1
                if (self._consecutive[name] >= self._min_frames
                        and name not in self._confirmed_present):
                    self._confirmed_present.add(name)
                    elapsed = time.time() - self._session_start
                    if self._late_minutes > 0 and elapsed > self._late_minutes * 60:
                        self._late_set.add(name)

            self._last_locations   = locs_full
            self._last_names       = names
            self._last_confidences = confidences
            confirmed = len(self._confirmed_present)
            recog     = len([n for n in names if n not in ("Unknown", "?")])
            label = (f"{len(locs)} face(s)  ·  {recog} seen  ·  {confirmed} confirmed"
                     if locs else "No faces detected")
            self._safe_set(self._detect_lbl, text=label)
        except Exception:
            pass
        finally:
            self._detecting = False

    def _draw_boxes(self, bgr):
        for i, (top, right, bottom, left) in enumerate(self._last_locations):
            name      = self._last_names[i]       if i < len(self._last_names)       else "?"
            conf      = self._last_confidences[i] if i < len(self._last_confidences) else 0
            known     = name not in ("Unknown", "?")
            confirmed = known and name in self._confirmed_present
            frames_so_far = self._consecutive.get(name, 0) if known else 0

            if confirmed:
                color = (16, 185, 129)   # bright green
                label = f"{name} {conf}%"
            elif known:
                color = (200, 160, 50)   # yellow — seen but not yet confirmed
                label = f"{name} {conf}% [{frames_so_far}/{self._min_frames}]"
            else:
                color = (239, 68, 68)    # red — unknown
                label = name

            cv2.rectangle(bgr, (left, top), (right, bottom), color, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.55, 1)
            cv2.rectangle(bgr, (left, top - th - 14), (left + tw + 10, top), color, -1)
            cv2.putText(bgr, label, (left + 5, top - 5),
                        cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1)
        ts = datetime.now().strftime("%H:%M:%S")
        cv2.putText(bgr, ts, (10, bgr.shape[0] - 10),
                    cv2.FONT_HERSHEY_PLAIN, 1.0, (107, 127, 163), 1)

    def _render(self, bgr):
        try:
            cw = max(self._canvas.winfo_width(),  1)
            ch = max(self._canvas.winfo_height(), 1)
            img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            img.thumbnail((cw, ch), Image.NEAREST)
            photo = ImageTk.PhotoImage(img)
            self._photo = photo
            self._canvas.delete("all")
            self._canvas.create_image(cw // 2, ch // 2, anchor="center", image=photo)
        except Exception:
            pass

    def _safe_set(self, widget, **kw):
        def _do():
            if self._running:
                try: widget.config(**kw)
                except Exception: pass
        try: self.after(0, _do)
        except Exception: pass

    def _capture(self):
        if self._current_frame is None:
            return
        try:
            self._btn_capture.config(state="disabled", text="⏳  Processing…")
        except Exception:
            pass
        frame    = self._current_frame.copy()
        save_dir = os.path.join(os.path.dirname(__file__), "..",
                                "input", "classroom_images")
        os.makedirs(save_dir, exist_ok=True)
        fname = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path  = os.path.join(save_dir, fname)
        cv2.imwrite(path, frame)
        confirmed = self._confirmed_present.copy()
        late      = self._late_set.copy()
        self._close()
        self._on_capture(path, confirmed, late)

    def _close(self):
        self._running = False
        try:
            if self._cap: self._cap.release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


# ── Main Application ──────────────────────────────────────────────────────────
class ClassEyeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ClassEye — Attendance System")
        self.configure(bg=BG)
        self.geometry("1340x800")
        self.minsize(1100, 680)

        self._image_path      = None
        self._pil_orig        = None
        self._pil_proc        = None
        self._orig_img        = None
        self._proc_img        = None
        self._students_all    = []
        self._present         = set()
        self._scanning        = False
        self._known_encodings = []
        self._known_names     = []
        self._cam_win              = None
        self._logo_img             = None
        self._late                 = set()
        self._camera_confirmed     = set()
        self._tolerance_val        = 0.5
        self._min_frames_val       = 3
        self._late_minutes_val     = 0

        self._style_ttk()
        self._build_ui()
        self._log("ClassEye ready.  Opening Live Camera…", "info")
        if BACKEND_OK:
            threading.Thread(target=self._preload_encodings, daemon=True).start()
        # Auto-open camera once the window is fully rendered
        if CV2_OK and FR_OK:
            self.after(150, self._open_camera)

    def _style_ttk(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Vertical.TScrollbar",
                    background=CARD2, troughcolor=SURFACE,
                    bordercolor=BORDER, arrowcolor=TEXT_DIM,
                    relief="flat", width=8)

    # ── Backend ───────────────────────────────────────────────────────────────
    def _preload_encodings(self):
        try:
            dataset = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "dataset")
            enc, names = load_known_faces(dataset)
            self._known_encodings = enc
            self._known_names     = names
            self._students_all    = sorted(set(names))
            self.after(0, lambda: self._log(
                f"Loaded {len(enc)} encoding(s) — {len(self._students_all)} student(s).", "ok"))
            self.after(0, self._refresh_roster)
        except Exception as e:
            self.after(0, lambda: self._log(f"Encoding preload failed: {e}", "warn"))

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_sidebar(body)
        self._build_center(body)
        self._build_roster(body)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        bar = tk.Frame(self, bg=SURFACE, height=60,
                       highlightthickness=1, highlightbackground=BORDER)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).convert("RGBA")
                img.thumbnail((40, 40), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(bar, image=self._logo_img, bg=SURFACE).pack(
                    side="left", padx=(16, 0), pady=10)
            except Exception:
                pass

        tk.Label(bar, text="ClassEye", bg=SURFACE, fg=TEXT,
                 font=(FONT, 15, "bold")).pack(side="left", padx=(8, 2), pady=14)
        tk.Label(bar, text="Attendance System", bg=SURFACE, fg=TEXT_DIM,
                 font=(FONT, 9)).pack(side="left", pady=18)

        # Right side: pills + clock
        self._clock_lbl = tk.Label(bar, bg=SURFACE, fg=TEXT_DIM, font=(FONT, 9))
        self._clock_lbl.pack(side="right", padx=20)
        self._tick_clock()

        pills = []
        if not CV2_OK:    pills.append(("No OpenCV", RED))
        elif not FR_OK:   pills.append(("No face_recognition", RED))
        if not BACKEND_OK: pills.append(("Demo mode", YELLOW))
        else:             pills.append(("Backend OK", GREEN))

        for txt, col in pills:
            pill = tk.Frame(bar, bg=col, padx=10, pady=3)
            pill.pack(side="right", padx=(0, 8), pady=20)
            tk.Label(pill, text=txt, bg=col, fg=BG,
                     font=(FONT, 8, "bold")).pack()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=BG, width=230)
        side.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=16)
        side.grid_propagate(False)

        def section(text):
            f = tk.Frame(side, bg=BG)
            f.pack(fill="x", pady=(14, 6))
            tk.Label(f, text=text, bg=BG, fg=TEXT_DIM,
                     font=(FONT, 7, "bold")).pack(side="left")
            tk.Frame(f, bg=BORDER, height=1).pack(
                side="left", fill="x", expand=True, padx=(8, 0))

        # ── Actions ───────────────────────────────────────────────────────────
        section("ACTIONS")

        self._btn_load = ModernButton(side, "Load Image", self._load_image,
                                      bg=ACCENT, icon="📂")
        self._btn_load.pack(fill="x", pady=(0, 5))

        cam_bg = GREEN if CV2_OK and FR_OK else BORDER2
        self._btn_camera = ModernButton(side, "Live Camera", self._open_camera,
                                         bg=cam_bg, icon="📷")
        self._btn_camera.pack(fill="x", pady=(0, 5))
        if not (CV2_OK and FR_OK):
            self._btn_camera.set_state("disabled")

        self._btn_scan = ModernButton(side, "Scan Faces", self._start_scan,
                                       bg=ACCENT, icon="🔍")
        self._btn_scan.pack(fill="x", pady=(0, 5))
        self._btn_scan.set_state("disabled")

        self._btn_export = ModernButton(side, "Export Excel", self._export,
                                         bg="#d97706", icon="📤")
        self._btn_export.pack(fill="x", pady=(0, 5))
        self._btn_export.set_state("disabled")

        self._btn_reset = ModernButton(side, "Reset Session", self._reset,
                                        bg=CARD2, fg=TEXT_MID, icon="↺")
        self._btn_reset.pack(fill="x", pady=(0, 0))

        # ── Progress ──────────────────────────────────────────────────────────
        section("PROGRESS")

        prog_bg = tk.Frame(side, bg=BORDER, height=5)
        prog_bg.pack(fill="x", pady=(0, 4))
        prog_bg.pack_propagate(False)
        self._prog_fill = tk.Frame(prog_bg, bg=ACCENT, width=0)
        self._prog_fill.place(x=0, y=0, relheight=1)

        self._prog_lbl = tk.Label(side, text="Idle  0%", bg=BG, fg=TEXT_DIM,
                                   font=(FONT, 8))
        self._prog_lbl.pack(anchor="w")

        # ── Statistics ────────────────────────────────────────────────────────
        section("STATISTICS")

        grid = tk.Frame(side, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self._stat_total   = StatTile(grid, "Total",   "—", ACCENT,  "👥")
        self._stat_present = StatTile(grid, "Present", "—", GREEN,   "✓")
        self._stat_absent  = StatTile(grid, "Absent",  "—", RED,     "✗")
        self._stat_rate    = StatTile(grid, "Rate",    "—", YELLOW,  "%")

        self._stat_total.grid(  row=0, column=0, sticky="nsew", padx=(0,4), pady=(0,4))
        self._stat_present.grid(row=0, column=1, sticky="nsew", padx=(4,0), pady=(0,4))
        self._stat_absent.grid( row=1, column=0, sticky="nsew", padx=(0,4))
        self._stat_rate.grid(   row=1, column=1, sticky="nsew", padx=(4,0))

        # ── Settings ──────────────────────────────────────────────────────────
        section("SETTINGS")

        def _make_slider(lbl_text, init, from_, to, step, fmt, on_change):
            row = tk.Frame(side, bg=BG)
            row.pack(fill="x", pady=(0, 8))
            top = tk.Frame(row, bg=BG)
            top.pack(fill="x")
            tk.Label(top, text=lbl_text, bg=BG, fg=TEXT_MID,
                     font=(FONT, 8)).pack(side="left")
            val_lbl = tk.Label(top, text=fmt(init), bg=BG, fg=TEXT,
                               font=(FONT, 8, "bold"))
            val_lbl.pack(side="right")
            def cb(v, l=val_lbl, f=fmt, c=on_change):
                c(float(v))
                l.config(text=f(float(v)))
            tk.Scale(row, from_=from_, to=to, resolution=step, orient="horizontal",
                     bg=BG, troughcolor=BORDER2, highlightthickness=0, bd=0,
                     showvalue=False, sliderlength=14, command=cb).pack(fill="x")

        _make_slider("Tolerance", self._tolerance_val, 0.3, 0.8, 0.05,
                     lambda v: f"{v:.2f}",
                     lambda v: setattr(self, '_tolerance_val', round(v, 2)))
        _make_slider("Min Frames", self._min_frames_val, 1, 10, 1,
                     lambda v: f"{int(v)} fr",
                     lambda v: setattr(self, '_min_frames_val', int(v)))
        _make_slider("Late after", self._late_minutes_val, 0, 30, 1,
                     lambda v: "Off" if int(v) == 0 else f"{int(v)} min",
                     lambda v: setattr(self, '_late_minutes_val', int(v)))

    # ── Center ────────────────────────────────────────────────────────────────
    def _build_center(self, parent):
        center = tk.Frame(parent, bg=BG)
        center.grid(row=0, column=1, sticky="nsew")
        center.rowconfigure(0, weight=3)
        center.rowconfigure(1, weight=1)
        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=1)

        def img_card(col, title, placeholder, attr_canvas):
            card = FlatCard(center)
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0, 6) if col == 0 else (6, 0), pady=(16, 6))
            card.rowconfigure(1, weight=1)
            card.columnconfigure(0, weight=1)

            hdr = tk.Frame(card, bg=CARD, pady=8)
            hdr.grid(row=0, column=0, sticky="ew", padx=12)
            tk.Frame(card, bg=BORDER, height=1).grid(
                row=0, column=0, sticky="ew", padx=0)

            lbl_frame = tk.Frame(card, bg=CARD, pady=8)
            lbl_frame.grid(row=0, column=0, sticky="ew", padx=12)
            tk.Label(lbl_frame, text=title, bg=CARD, fg=TEXT_MID,
                     font=(FONT, 9, "bold")).pack(side="left")

            c = tk.Canvas(card, bg="#060b12", highlightthickness=0)
            c.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
            setattr(self, attr_canvas, c)
            self._draw_placeholder(c, placeholder)
            return c

        c_orig = img_card(0, "Captured Image",   "No image loaded",        "_canvas_orig")
        c_proc = img_card(1, "Processed Output", "Run scan to see output", "_canvas_proc")
        c_orig.bind("<Configure>", lambda e: self._on_canvas_resize(self._canvas_orig))
        c_proc.bind("<Configure>", lambda e: self._on_canvas_resize(self._canvas_proc))

        # Log panel
        log_card = FlatCard(center)
        log_card.grid(row=1, column=0, columnspan=2,
                      sticky="nsew", pady=(6, 16))
        log_card.rowconfigure(1, weight=1)
        log_card.columnconfigure(0, weight=1)

        log_hdr = tk.Frame(log_card, bg=CARD, pady=8, padx=12)
        log_hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(log_hdr, text="System Log", bg=CARD, fg=TEXT_MID,
                 font=(FONT, 9, "bold")).pack(side="left")
        PulsingDot(log_hdr, color=GREEN).pack(side="left", padx=8)
        self._scan_time_lbl = tk.Label(log_hdr, text="", bg=CARD,
                                        fg=TEXT_DIM, font=(FONT, 8))
        self._scan_time_lbl.pack(side="right")

        tk.Frame(log_card, bg=BORDER, height=1).grid(
            row=0, column=0, sticky="ew", padx=0)

        self._log_text = tk.Text(log_card, bg="#060b12", fg=TEXT_DIM,
                                  font=("Consolas", 8), bd=0,
                                  highlightthickness=0, state="disabled",
                                  height=5, wrap="word", insertbackground=TEXT)
        self._log_text.grid(row=1, column=0, sticky="nsew", padx=6, pady=(4, 6))
        sb = ttk.Scrollbar(log_card, style="Vertical.TScrollbar",
                           command=self._log_text.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=(4, 6))
        self._log_text.config(yscrollcommand=sb.set)
        self._log_text.tag_config("ok",   foreground=GREEN)
        self._log_text.tag_config("warn", foreground=YELLOW)
        self._log_text.tag_config("err",  foreground=RED)
        self._log_text.tag_config("info", foreground=ACCENT_H)

    # ── Roster ────────────────────────────────────────────────────────────────
    def _build_roster(self, parent):
        roster = FlatCard(parent)
        roster.grid(row=0, column=2, sticky="nsew", padx=(12, 0), pady=16)
        roster.rowconfigure(3, weight=1)
        roster.columnconfigure(0, weight=1)
        roster.config(width=250)

        # Header
        rh = tk.Frame(roster, bg=CARD, pady=10, padx=14)
        rh.grid(row=0, column=0, sticky="ew")
        tk.Label(rh, text="Student Roster", bg=CARD, fg=TEXT,
                 font=(FONT, 10, "bold")).pack(side="left")
        self._roster_count = tk.Label(rh, text="", bg=ACCENT, fg=TEXT,
                                       font=(FONT, 8, "bold"), padx=7, pady=1)
        self._roster_count.pack(side="right")

        tk.Frame(roster, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew")

        # Filter tabs
        tab_frame = tk.Frame(roster, bg=CARD, pady=6, padx=10)
        tab_frame.grid(row=2, column=0, sticky="ew")
        self._filter_var = tk.StringVar(value="all")
        self._filter_btns = {}
        for txt, val in [("All", "all"), ("Present", "present"), ("Late", "late"), ("Absent", "absent")]:
            b = tk.Label(tab_frame, text=txt, bg=CARD2, fg=TEXT_MID,
                          font=(FONT, 8, "bold"), padx=10, pady=4, cursor="hand2")
            b.pack(side="left", padx=(0, 4))
            b.bind("<Button-1>", lambda e, v=val: self._set_filter(v))
            self._filter_btns[val] = b
        self._set_filter("all", refresh=False)

        # List
        lf = tk.Frame(roster, bg=CARD)
        lf.grid(row=3, column=0, sticky="nsew", padx=6, pady=(4, 6))
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)

        self._roster_canvas = tk.Canvas(lf, bg=CARD, highlightthickness=0)
        self._roster_canvas.grid(row=0, column=0, sticky="nsew")
        rsb = ttk.Scrollbar(lf, style="Vertical.TScrollbar",
                            orient="vertical", command=self._roster_canvas.yview)
        rsb.grid(row=0, column=1, sticky="ns")
        self._roster_canvas.config(yscrollcommand=rsb.set)

        self._roster_inner = tk.Frame(self._roster_canvas, bg=CARD)
        self._roster_win   = self._roster_canvas.create_window(
            (0, 0), window=self._roster_inner, anchor="nw")
        self._roster_inner.bind("<Configure>", self._on_roster_configure)
        self._roster_canvas.bind("<Configure>", self._on_roster_canvas_configure)

    def _on_roster_configure(self, _):
        self._roster_canvas.configure(
            scrollregion=self._roster_canvas.bbox("all"))

    def _on_roster_canvas_configure(self, e):
        self._roster_canvas.itemconfig(self._roster_win, width=e.width)

    def _set_filter(self, val, refresh=True):
        self._filter_var.set(val)
        for k, b in self._filter_btns.items():
            if k == val:
                b.config(bg=ACCENT, fg=TEXT)
            else:
                b.config(bg=CARD2, fg=TEXT_MID)
        if refresh:
            self._refresh_roster()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _draw_placeholder(self, canvas, msg):
        canvas.update_idletasks()
        w = canvas.winfo_width()  or 400
        h = canvas.winfo_height() or 300
        canvas.delete("all")
        canvas.create_rectangle(0, 0, w, h, fill="#060b12", outline="")
        # Dashed border
        canvas.create_rectangle(20, 20, w-20, h-20,
                                 outline=BORDER2, dash=(4, 4))
        canvas.create_text(w//2, h//2 - 10, text="⬜", fill=BORDER2,
                           font=(FONT, 28))
        canvas.create_text(w//2, h//2 + 24, text=msg, fill=TEXT_DIM,
                           font=(FONT, 10), justify="center")

    def _show_image(self, canvas, path, is_array=False):
        try:
            if is_array:
                pil = Image.fromarray(cv2.cvtColor(path, cv2.COLOR_BGR2RGB))
            else:
                pil = Image.open(path).copy()
            if canvas is self._canvas_orig:
                self._pil_orig = pil
            else:
                self._pil_proc = pil
            self._render_to_canvas(canvas, pil)
        except Exception as exc:
            self._log(f"Image display error: {exc}", "err")

    def _render_to_canvas(self, canvas, pil_img):
        try:
            canvas.update_idletasks()
            cw = max(canvas.winfo_width(),  1)
            ch = max(canvas.winfo_height(), 1)
            img = pil_img.copy()
            img.thumbnail((cw, ch), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            if canvas is self._canvas_orig:
                self._orig_img = photo
            else:
                self._proc_img = photo
            canvas.delete("all")
            canvas.create_image(cw//2, ch//2, anchor="center", image=photo)
        except Exception:
            pass

    def _on_canvas_resize(self, canvas):
        if canvas is self._canvas_orig:
            if self._pil_orig: self._render_to_canvas(canvas, self._pil_orig)
            else:              self._draw_placeholder(canvas, "No image loaded")
        elif canvas is self._canvas_proc:
            if self._pil_proc: self._render_to_canvas(canvas, self._pil_proc)
            else:              self._draw_placeholder(canvas, "Run scan to see output")

    def _tick_clock(self):
        self._clock_lbl.config(
            text=datetime.now().strftime("%a %d %b  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    def _log(self, msg, level="info"):
        ts   = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        self._log_text.config(state="normal")
        self._log_text.insert("end", line, level)
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _set_progress(self, pct, label):
        def _do():
            total = self._prog_fill.master.winfo_width()
            w     = max(1, int(total * pct / 100))
            color = GREEN if pct == 100 else (RED if label == "Error" else ACCENT)
            self._prog_fill.place(x=0, y=0, relheight=1, width=w)
            self._prog_fill.config(bg=color)
            self._prog_lbl.config(text=f"{label}  {pct}%")
        self.after(0, _do)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select Classroom Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All", "*.*")])
        if not path:
            return
        self._image_path = path
        self._log(f"Loaded: {os.path.basename(path)}")
        self._show_image(self._canvas_orig, path)
        self._pil_proc = None
        self._draw_placeholder(self._canvas_proc, "Run scan to see output")
        self._btn_scan.set_state("normal")
        self._btn_export.set_state("disabled")
        self._present.clear()
        self._refresh_roster()
        self._reset_stats()

    def _open_camera(self):
        if self._cam_win and self._cam_win.winfo_exists():
            self._cam_win.lift()
            return
        if not CV2_OK:
            messagebox.showerror("Missing library",
                                 "OpenCV not installed.\n\npip install opencv-python")
            return
        if not FR_OK:
            messagebox.showerror("Missing library",
                                 "face_recognition not installed.\n\n"
                                 "pip install face-recognition")
            return
        self._log("Opening live camera…")
        self._cam_win = CameraWindow(
            self,
            on_capture=self._on_camera_capture,
            known_encodings=self._known_encodings,
            known_names=self._known_names,
            tolerance=self._tolerance_val,
            min_frames=self._min_frames_val,
            late_minutes=self._late_minutes_val,
        )

    def _on_camera_capture(self, image_path, confirmed_present=None, late_set=None):
        self._image_path = image_path
        if confirmed_present:
            self._camera_confirmed = set(confirmed_present)
            self._late             = set(late_set or [])
            self._log(
                f"Frame captured: {os.path.basename(image_path)} — "
                f"{len(confirmed_present)} confirmed by camera.", "ok")
        else:
            self._camera_confirmed = set()
            self._late.clear()
            self._log(f"Frame captured: {os.path.basename(image_path)}")
        self._present.clear()
        self._show_image(self._canvas_orig, image_path)
        self._pil_proc = None
        self._draw_placeholder(self._canvas_proc, "Run scan to see output")
        self._btn_scan.set_state("normal")
        self._btn_export.set_state("disabled")
        self._refresh_roster()
        self._reset_stats()
        self._start_scan()

    def _start_scan(self):
        if self._scanning:
            return
        self._scanning = True
        self._btn_scan.set_state("disabled")
        self._btn_load.set_state("disabled")
        self._btn_camera.set_state("disabled")
        self._set_progress(0, "Initialising")
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        t0 = time.time()
        try:
            self._log("Starting face recognition pipeline…")
            self._set_progress(15, "Loading encodings")

            # If encodings haven't loaded yet (preload thread still running),
            # load them now so _students_all is always populated before we mark attendance
            if BACKEND_OK and not self._students_all:
                enc, names = load_known_faces()
                self._known_encodings = enc
                self._known_names     = names
                self._students_all    = sorted(set(names))
                self.after(0, lambda: self._log(
                    f"Loaded {len(enc)} encoding(s) — "
                    f"{len(self._students_all)} student(s) in class.", "ok"))
                self.after(0, self._refresh_roster)

            if BACKEND_OK:
                self._set_progress(35, "Detecting faces")
                present = recognize_students(self._image_path, tolerance=self._tolerance_val)
                self._set_progress(75, "Matching identities")
            else:
                self._log("Demo mode — backend not available.", "warn")
                time.sleep(1.5)
                present = ["Student_A", "Student_B"]

            scan_present  = set(p for p in present if p != "Unknown")
            self._present = scan_present | self._camera_confirmed
            self._set_progress(90, "Building report")

            if BACKEND_OK:
                base   = os.path.splitext(os.path.basename(self._image_path))[0]
                ext    = os.path.splitext(self._image_path)[1]
                outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "output", "processed_images")
                proc   = os.path.join(outdir, f"processed_{base}{ext}")
                if os.path.exists(proc):
                    self.after(0, lambda: self._show_image(self._canvas_proc, proc))

            absent  = [s for s in self._students_all if s not in self._present]
            elapsed = time.time() - t0
            self._log(
                f"Scan complete in {elapsed:.1f}s — "
                f"{len(self._present)} present, {len(absent)} absent.", "ok")
            self.after(0, lambda: self._scan_time_lbl.config(
                text=f"Last scan: {datetime.now().strftime('%H:%M:%S')} ({elapsed:.1f}s)"))

            # Save with full class list so absent students appear in the Excel
            mark_attendance(list(self._present), all_students=self._students_all)
            self._set_progress(100, "Done")
            self.after(0, self._scan_done)

        except Exception as exc:
            self._log(f"Scan failed: {exc}", "err")
            self._set_progress(0, "Error")
            self.after(0, self._scan_done)

    def _scan_done(self):
        self._scanning = False
        self._btn_scan.set_state("normal")
        self._btn_load.set_state("normal")
        if CV2_OK and FR_OK:
            self._btn_camera.set_state("normal")
        self._btn_export.set_state("normal")
        self._refresh_roster()
        self._update_stats()

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if not path:
            return
        try:
            import pandas as pd
            names = sorted(self._students_all) or sorted(self._present)
            rows = [{"Name": n,
                     "Status": ("Late" if n in self._late else "Present")
                               if n in self._present else "Absent",
                     "Date": datetime.now().strftime("%Y-%m-%d"),
                     "Time": datetime.now().strftime("%H:%M:%S")}
                    for n in names]
            df = pd.DataFrame(rows)
            if path.endswith(".csv"):
                df.to_csv(path, index=False)
            else:
                df.to_excel(path, index=False)
            self._log(f"Exported → {os.path.basename(path)}", "ok")
            messagebox.showinfo("Export complete", f"Saved to:\n{path}")
        except ImportError:
            self._log("pandas not installed.", "err")
        except Exception as exc:
            self._log(f"Export error: {exc}", "err")

    def _reset(self):
        self._image_path = None
        self._present.clear()
        self._late.clear()
        self._camera_confirmed.clear()
        self._pil_orig = None
        self._pil_proc = None
        self._draw_placeholder(self._canvas_orig, "No image loaded")
        self._draw_placeholder(self._canvas_proc, "Run scan to see output")
        self._btn_scan.set_state("disabled")
        self._btn_export.set_state("disabled")
        self._set_progress(0, "Idle")
        self._refresh_roster()
        self._reset_stats()
        self._log("Session reset.")

    # ── Roster ────────────────────────────────────────────────────────────────
    def _refresh_roster(self):
        for w in self._roster_inner.winfo_children():
            w.destroy()
        filt  = self._filter_var.get()
        names = sorted(self._students_all) if self._students_all else sorted(self._present)

        shown = [n for n in names
                 if not (filt == "present" and (n not in self._present or n in self._late))
                 and not (filt == "late"    and n not in self._late)
                 and not (filt == "absent"  and n in self._present)]

        self._roster_count.config(text=f" {len(shown)} ")

        if not names:
            tk.Label(self._roster_inner, text="No students loaded yet",
                     bg=CARD, fg=TEXT_DIM, font=(FONT, 9)).pack(pady=24)
            return
        if not shown:
            tk.Label(self._roster_inner, text="No matches",
                     bg=CARD, fg=TEXT_DIM, font=(FONT, 9)).pack(pady=24)
            return

        for name in shown:
            present = name in self._present
            late    = name in self._late
            if late:
                dot_color  = YELLOW
                badge_bg   = "#2a2010"
                badge_fg   = YELLOW
                badge_text = "Late"
                border_col = "#3a3010"
            elif present:
                dot_color  = GREEN
                badge_bg   = "#1a3a2a"
                badge_fg   = GREEN
                badge_text = "Present"
                border_col = "#1a3a2a"
            else:
                dot_color  = RED
                badge_bg   = "#2a1a1a"
                badge_fg   = RED
                badge_text = "Absent"
                border_col = BORDER

            row = tk.Frame(self._roster_inner, bg=SURFACE, pady=7, padx=10,
                           highlightthickness=1, highlightbackground=border_col)
            row.pack(fill="x", pady=2, padx=4)
            tk.Frame(row, bg=dot_color, width=6, height=6).pack(
                side="left", padx=(0, 10))
            tk.Label(row, text=name, bg=SURFACE, fg=TEXT,
                     font=(FONT, 9)).pack(side="left", fill="x", expand=True)
            badge = tk.Frame(row, bg=badge_bg, padx=8, pady=2)
            badge.pack(side="right")
            tk.Label(badge, text=badge_text, bg=badge_bg, fg=badge_fg,
                     font=(FONT, 8, "bold")).pack()

    # ── Stats ─────────────────────────────────────────────────────────────────
    def _update_stats(self):
        names   = self._students_all or sorted(self._present)
        total   = max(len(names), len(self._present))
        present = len(self._present)
        absent  = total - present
        rate    = f"{present / total * 100:.0f}%" if total else "—"
        self._stat_total.set(total)
        self._stat_present.set(present)
        self._stat_absent.set(absent)
        self._stat_rate.set(rate)

    def _reset_stats(self):
        for s in (self._stat_total, self._stat_present,
                  self._stat_absent, self._stat_rate):
            s.set("—")


# ── Entry point ───────────────────────────────────────────────────────────────
def launch():
    app = ClassEyeApp()
    app.mainloop()

if __name__ == "__main__":
    launch()
