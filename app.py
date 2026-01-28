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


def start_download(url_entry, format_var, status, button, log_box, stats):
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

    fmt = format_var.get()
    output_path = filedialog.asksaveasfilename(
        defaultextension=f".{fmt}",
        filetypes=[(fmt.upper(), f"*.{fmt}")],
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
    root.geometry("820x560")
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
    
    def styled_button(parent, text, command):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=accent,
            fg="white",
            activebackground="#388bfd",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )

        def on_enter(e):
            btn.config(bg="#388bfd")

        def on_leave(e):
            btn.config(bg=accent)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn


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

    label("Output Format:").pack(pady=4)

    format_var = tk.StringVar(value="mp4")
    formats = ["mp4", "mov", "webm", "mkv"]

    option = tk.OptionMenu(root, format_var, *formats)
    option.config(
        bg="#161b22",
        fg=fg,
        activebackground="#21262d",
        activeforeground=fg,
        highlightthickness=0,
        relief="flat",
        font=("Segoe UI", 10),
        cursor="hand2"
    )
    option["menu"].config(
        bg="#161b22",
        fg=fg,
        activebackground="#1f6feb",
        activeforeground="white",
        relief="flat"
    )
    option.pack(pady=4)


    status = label("Idle", fg="#9da5b4")
    status.pack(pady=4)

    btn = styled_button(
        root,
        "Start Download",
        lambda: start_download(
            url_entry, format_var, status, btn, log_box, stats
        )
    )
    btn.pack(pady=10)

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
