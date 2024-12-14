import tkinter as tk
from tkinter import ttk
import vlc
import requests
import os

# Create the main window
root = tk.Tk()
root.title("CH3")
root.geometry("800x600")

# Create VLC (Mediaplayer) instance and player
instance = vlc.Instance()
player = instance.media_player_new()

# Control frame for buttons
control_frame = tk.Frame(root)
control_frame.pack(side=tk.TOP, fill=tk.X)

# Volume display label
volume_label = tk.Label(control_frame, text="Volume: 50%", font=("Arial", 10, "bold"))
volume_label.pack(side=tk.RIGHT, padx=10)

# Video frame
canvas = tk.Canvas(root)
canvas.pack(expand=True, fill=tk.BOTH)

# Guide canvas
guide_canvas = tk.Canvas(root, bg="white")
guide_canvas.place_forget()

# Function to create gradient background
def create_gradient(canvas, width, height, color1, color2):
    r1, g1, b1 = root.winfo_rgb(color1)
    r2, g2, b2 = root.winfo_rgb(color2)
    r_ratio = (r2 - r1) / height
    g_ratio = (g2 - g1) / height
    b_ratio = (b2 - b1) / height

    for i in range(height):
        nr = int(r1 + (r_ratio * i))
        ng = int(g1 + (g_ratio * i))
        nb = int(b1 + (b_ratio * i))
        color = f'#{nr:04x}{ng:04x}{nb:04x}'
        canvas.create_line(0, i, width, i, fill=color)

# Title overlay
title_overlay_frame = tk.Frame(root, bg="black", height=120)
title_overlay_frame.place(relx=0.5, rely=1.0, anchor=tk.S, relwidth=1.0, height=120)

# Create canvas for gradient
title_canvas = tk.Canvas(title_overlay_frame, height=120)
title_canvas.pack(fill=tk.BOTH, expand=True)

# Apply gradient background
create_gradient(title_canvas, 800, 120, "black", "#333")

title_label = tk.Label(title_canvas, text="", font=("Arial", 20, "bold"), fg="white", bg="#333", pady=20)
title_label.pack(fill=tk.BOTH)

title_overlay_frame.lower() # Start with the overlay hidden

# Playlist and current index
playlist = []
current_index = 0
index_file = "last_index.txt"
volume_file = "volume_level.txt"

# Function to fetch and parse the playlist
def fetch_playlist(url):
    global playlist
    response = requests.get(url)
    lines = response.text.splitlines()
    current_title = None
    for line in lines:
        if line.startswith("#EXTINF:"):
            current_title = line.split(",", 1)[1].strip()
        elif line and not line.startswith("#"):
            playlist.append({"url": line, "title": current_title})
    return playlist

# Function to cehck if a stream URL is available 
def is_stream_available(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Function to preload media
def preload_media(url):
    try:
        media = instance.media_new(url)
        return media
    except Exception as e:
        print(f"Error preloading media: {e}")
        return None

# Function to show title overlay
def show_title_overlay(text):
    title_label.config(text=text)
    title_overlay_frame.lift()
    root.after(3000, hide_title_overlay) # Hide after 3 seconds

#Function to hide title overlay
def hide_title_overlay():
    title_overlay_frame.lower()
    
# Function to play media
def play_media(index):
    global current_index
    if playlist:
        while index < len(playlist):
                if is_stream_available(playlist[index]["url"]):
                    current_index = index
                    media = preload_media(playlist[current_index]["url"])
                    if media:
                        player.set_media(media)
                        player.set_hwnd(canvas.winfo_id())
                        player.play()
                        show_title_overlay(f"{playlist[current_index]['title']}")
                        return
                index += 1 
    
# Function to play the next media
def next_media():
    global current_index
    play_media(current_index + 1)

# Function to play previous media
def previous_media():
    global current_index
    play_media(current_index - 1)

# Function to increase volume
def increase_volume():
    current_volume = player.audio_get_volume()
    new_volume = min(current_volume + 1, 100)
    player.audio_set_volume(new_volume)
    volume_label.config(text=f"Volume:{new_volume}%")
    save_volume(new_volume)

# Function to decrease volume
def decrease_volume():
    current_volume = player.audio_get_volume()
    new_volume = max(current_volume - 1, 0)
    player.audio_set_volume(new_volume)
    volume_label.config(text=f"Volume: {new_volume}%")
    save_volume(new_volume)

# Save the current volume level to a file
def save_volume(volume):
    with open(volume_file, "w") as file:
        file.write(str(volume))

# Load the last volume level from a file
def load_volume():
    if os.path.exists(volume_file):
        with open(volume_file, "r") as file:
            return int(file.read())
    return 50 # Default volume level if file doesn't exist

# Save the current index to a file
def save_current_index():
    with open(index_file, "w") as file:
        file.write(str(current_index))

# Load the last saved index from a file
def load_last_index():
    if os.path.exists(index_file):
        with open(index_file, "r") as file:
            return int(file.read())
    return 0

# Function to show playlist guide
def show_guide():
    guide_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
    guide_canvas.delete("all")

    guide_frame = tk.Frame(guide_canvas)
    guide_canvas.create_window((0, 0), window=guide_frame, anchor="nw")

    scrollbar = ttk.Scrollbar(guide_canvas, orient=tk.VERTICAL, command=guide_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    for index, item in enumerate(playlist):
        guide_label = tk.Label(guide_frame, text=f"{index + 1}: {item['title']}", anchor="w", padx=10, pady=5)
        guide_label.pack(fill=tk.X)
        guide_label.bind("<Button-1>", lambda e, idx=index: select_playlist(idx))

    guide_frame.update_idletasks()
    guide_canvas.config(scrollregion=guide_canvas.bbox("all"))
    guide_canvas.config(yscrollcommand=scrollbar.set)

def hide_guide():
    guide_canvas.place_forget()

# Function to select playlist from the guide
def select_playlist(index):
    hide_guide()
    play_media(index)

# Function to handle index input
def handle_index_input():
    index_str = index_entry.get()
    try:
        index = int(index_str) - 1
        if 0 <= index < len(playlist):
            play_media(index)
        else:
            print("Index out of range")
    except ValueError:
        print("Invalid Index")

# Fetch and play the playlist on startup
playlist_url = "https://iptv-org.github.io/iptv/index.m3u"
fetch_playlist(playlist_url)
last_index = load_last_index()
play_media(last_index)

# Load the saved volume level
saved_volume = load_volume()
player.audio_set_volume(saved_volume)
volume_label.config(text=f"Volume: {saved_volume}%")

# Control buttons (optional for navigation)
btn_prev = ttk.Button(control_frame, text="Previous", command=previous_media)
btn_prev.pack(side=tk.LEFT, padx=10, pady=5)

btn_next = ttk.Button(control_frame, text="Next", command=next_media)
btn_next.pack(side=tk.RIGHT, padx=10, pady=5)

# Volume buttons
btn_vol_up = ttk.Button(control_frame, text="Volume +", command=increase_volume)
btn_vol_up.pack(side=tk.RIGHT, padx=10)

btn_vol_down = ttk.Button(control_frame, text="Volume -", command=decrease_volume)
btn_vol_down.pack(side=tk.RIGHT, padx=10)

# Guide button
btn_guide = ttk.Button(control_frame, text="Guide", command=show_guide)
btn_guide.pack(side=tk.LEFT, padx=10)

# Index input entry and button
index_entry = ttk.Entry(control_frame, width=5)
index_entry.pack(side=tk.LEFT, padx=10)

btn_go = ttk.Button(control_frame, text="Go", command=handle_index_input)
btn_go.pack(side=tk.LEFT, padx=10)

# Event to save the current index when the window is closed
def on_closing():
    save_current_index()
    save_volume(player.audio_get_volume())
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter event loop
root.mainloop()