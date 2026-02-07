import threading
import queue
import yt_dlp
import customtkinter as ctk
from tkinter import filedialog

# ================= LOGGER =================
class GuiLogger:
    def __init__(self, log_queue):
        self.log_queue = log_queue
    def debug(self, msg): self.log_queue.put(msg)
    def info(self, msg): self.log_queue.put(msg)
    def warning(self, msg): self.log_queue.put(f"[WARN] {msg}")
    def error(self, msg): self.log_queue.put(f"[ERROR] {msg}")


# ================= DOWNLOAD =================
def download_audio(url, output_dir, log_queue):
    logger = GuiLogger(log_queue)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }],
        "logger": logger,
        "progress_hooks": [
            lambda d: log_queue.put(
                f"{d.get('_percent_str','')} | {d.get('_speed_str','')} | ETA {d.get('_eta_str','')}"
            ) if d["status"] == "downloading" else None
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        log_queue.put("✔ Finished")
    except Exception as e:
        log_queue.put(f"✖ {e}")


# ================= APP =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YT Audio Downloader")
        self.geometry("840x580")

        self.log_queue = queue.Queue()

        # ---------- COLORS ----------
        self.ACCENT = "#7aa2f7"
        self.SECONDARY = "#64748b"
        self.TEXT = "#cbd5e1"
        self.CARD = "#020617"
        self.BG = "#0f172a"

        self.configure(fg_color=self.BG)

        # ---------- MAIN ----------
        container = ctk.CTkFrame(
            self,
            corner_radius=22,
            fg_color=self.CARD
        )
        container.pack(fill="both", expand=True, padx=24, pady=24)

        title = ctk.CTkLabel(
            container,
            text="YouTube Audio Downloader",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.TEXT
        )
        title.pack(pady=(18, 10))

        self.url_card(container)
        self.output_card(container)
        self.console_card(container)

        self.after(100, self.update_console)

    # ---------- UI SECTIONS ----------
    def url_card(self, parent):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=self.BG,
            border_width=1,
            border_color=self.SECONDARY
        )
        frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            frame,
            text="YouTube URL",
            text_color=self.SECONDARY,
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=14, pady=(10, 0))

        self.url_entry = ctk.CTkEntry(
            frame,
            height=40,
            placeholder_text="https://youtube.com/watch?v=...",
            fg_color=self.CARD,
            border_color=self.SECONDARY,
            text_color=self.TEXT
        )
        self.url_entry.pack(fill="x", padx=14, pady=12)

    def output_card(self, parent):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=self.BG,
            border_width=1,
            border_color=self.SECONDARY
        )
        frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            frame,
            text="Output",
            text_color=self.SECONDARY,
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=14, pady=(10, 0))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=12)

        self.folder_entry = ctk.CTkEntry(
            row,
            height=40,
            placeholder_text="Destination folder",
            fg_color=self.CARD,
            border_color=self.SECONDARY,
            text_color=self.TEXT
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            row,
            text="📁",
            width=52,
            fg_color=self.SECONDARY,
            hover_color="#475569",
            text_color=self.TEXT,
            command=self.choose_folder
        ).pack(side="right")

        ctk.CTkButton(
            frame,
            text="Download",
            height=44,
            fg_color=self.ACCENT,
            hover_color="#5b8def",
            text_color="#020617",
            font=ctk.CTkFont(weight="bold"),
            command=self.start_download
        ).pack(fill="x", padx=14, pady=(0, 14))

    def console_card(self, parent):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=self.BG,
            border_width=1,
            border_color=self.SECONDARY
        )
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            frame,
            text="Console",
            text_color=self.SECONDARY,
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=14, pady=(10, 0))

        self.console = ctk.CTkTextbox(
            frame,
            font=("Consolas", 12),
            fg_color=self.CARD,
            text_color=self.TEXT
        )
        self.console.pack(fill="both", expand=True, padx=14, pady=12)
        self.console.configure(state="disabled")

    # ---------- ACTIONS ----------
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)

    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()

        if not url or not folder:
            self.log_queue.put("✖ Missing URL or folder")
            return

        self.log_queue.put("▶ Downloading...")
        threading.Thread(
            target=download_audio,
            args=(url, folder, self.log_queue),
            daemon=True
        ).start()

    def update_console(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.console.configure(state="normal")
            self.console.insert("end", msg + "\n")
            self.console.see("end")
            self.console.configure(state="disabled")
        self.after(100, self.update_console)


# ================= RUN =================
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    App().mainloop()
