import subprocess
import shutil
import os
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import re

# Header so that you dont get blocked by bot protection, DO NOT REMOVE, TOOL WONT WORK WITHOUT IT [SOME SITES WONT WORK WITH OR WITHOUT IT]
HEADERS = (
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
    "Referer: https://videos-uploader.com/\r\n"
)

TIME_RE = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
BITRATE_RE = re.compile(r"bitrate=\s*([\dk\.]+bits/s)")
SPEED_RE = re.compile(r"speed=\s*([\d\.]+x)")

ffmpeg_path_cache = None

def find_ffmpeg():
    global ffmpeg_path_cache

    if ffmpeg_path_cache and os.path.exists(ffmpeg_path_cache):
        return ffmpeg_path_cache

    if os.path.exists("ffmpeg.exe"):
        ffmpeg_path_cache = os.path.abspath("ffmpeg.exe")
        return ffmpeg_path_cache

    path = shutil.which("ffmpeg")
    if path:
        ffmpeg_path_cache = path
        return path

    return None


def ask_for_ffmpeg():
    global ffmpeg_path_cache
    path = filedialog.askopenfilename(
        title="Select ffmpeg.exe",
        filetypes=[("FFmpeg", "ffmpeg.exe")]
    )
    if path:
        ffmpeg_path_cache = path
        return path
    return None


def log(box, text):
    box.insert(tk.END, text + "\n")
    box.see(tk.END)


def update_stats(label, t, b, s):
    label.config(
        text=f"Time: {t or '--'}   |   Bitrate: {b or '--'}   |   Speed: {s or '--'}"
    )

def download_video(ffmpeg, url, output_path, status, button, log_box, stats):
    try:
        status.config(text="Downloading...")

        cmd = [
            ffmpeg,
            "-y",
            "-headers", HEADERS,
            "-i", url,
            "-c", "copy",
            output_path
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        t = b = s = None

        for line in process.stdout:
            line = line.rstrip()
            log(log_box, line)

            if m := TIME_RE.search(line):
                t = m.group(1)
            if m := BITRATE_RE.search(line):
                b = m.group(1)
            if m := SPEED_RE.search(line):
                s = m.group(1)

            stats.after(0, update_stats, stats, t, b, s)

        process.wait()

        if process.returncode != 0:
            raise RuntimeError("FFmpeg exited with an error")

        status.config(text="Done ✔")
        update_stats(stats, "Completed", "-", "-")
        messagebox.showinfo("Success", f"Saved to:\n{output_path}")

    except Exception as e:
        status.config(text="Failed ❌")
        log(log_box, f"[ERROR] {e}")
        messagebox.showerror("Error", str(e))

    finally:
        button.config(state="normal")

def start_download(url_entry, status, button, log_box, stats):
    url = url_entry.get().strip()
    log_box.delete("1.0", tk.END)
    update_stats(stats, "--", "--", "--")

    if not url:
        messagebox.showwarning("Input Error", "Please enter a video URL.")
        return

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        if not messagebox.askyesno(
            "FFmpeg Not Found",
            "FFmpeg was not found.\nDo you want to locate ffmpeg.exe manually?"
        ):
            return

        ffmpeg = ask_for_ffmpeg()
        if not ffmpeg:
            return

    output_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 Video", "*.mp4")],
        title="Save video as"
    )

    if not output_path:
        return

    button.config(state="disabled")

    threading.Thread(
        target=download_video,
        args=(ffmpeg, url, output_path, status, button, log_box, stats),
        daemon=True
    ).start()

def main():
    root = tk.Tk()
    root.title("m3u8 Video Downloader")
    root.geometry("820x520")
    root.resizable(False, False)

    bg = "#0f1115"
    fg = "#e6e6e6"
    accent = "#1f6feb"

    root.configure(bg=bg)

    def label(text, **kw):
        return tk.Label(
            root,
            text=text,
            bg=kw.pop("bg", bg),
            fg=kw.pop("fg", fg),
            **kw
        )

    label("Video URL:").pack(pady=6)

    url_entry = tk.Entry(
        root,
        width=100,
        bg="#161b22",
        fg=fg,
        insertbackground=fg,
        relief="flat"
    )
    url_entry.pack(pady=4)

    status = label("Idle", fg="#9da5b4")
    status.pack(pady=4)

    btn = tk.Button(
        root,
        text="Start Download",
        width=22,
        bg=accent,
        fg="white",
        relief="flat",
        command=lambda: start_download(
            url_entry, status, btn, log_box, stats
        )
    )
    btn.pack(pady=6)

    stats = label(
        "Time: --   |   Bitrate: --   |   Speed: --",
        font=("Segoe UI", 10, "bold")
    )
    stats.pack(pady=6)

    log_box = scrolledtext.ScrolledText(
        root,
        width=100,
        height=16,
        bg="#010409",
        fg="#c9d1d9",
        insertbackground=fg,
        relief="flat"
    )
    log_box.pack(padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()