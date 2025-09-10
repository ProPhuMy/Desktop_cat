import os
import sys
import random
import tkinter as tk
from tkinter import scrolledtext
import google.generativeai as genai  # <<< ADDED: Gemini library
import threading  # <<< ADDED: Library to run API calls in a separate thread to avoid blocking the GUI
import customtkinter as ctk

# --- Helper function for PyInstaller path handling ---
def resource_path(relative_path):
    """
    Get absolute path to resource, works for development and for PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class DesktopPetApp:
    def __init__(self, master):
        """
        Initializes the Desktop Pet application.
        """
        self.master = master
        self.master.config(highlightbackground='black')
        self.master.overrideredirect(True)
        self.master.wm_attributes('-transparentcolor', 'black')
        self.master.wm_attributes('-topmost', True)

        # Ensure geometry info is up-to-date
        self.master.update_idletasks()

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.x = screen_width // 2 - 50
        self.y = screen_height - 150

        # Ensure initial position is clamped to the visible area
        self.cycle = 0
        self.check = 0
        self.idle_num = [1, 2, 3, 4]
        self.sleep_num = [10, 11, 12, 13, 15]
        self.walk_left_num = [6, 7]
        self.walk_right_num = [8, 9]
        self.event_number = random.randrange(1, 3, 1)

        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.chat_window = None

        # Load GIF frames
        self.idle = [tk.PhotoImage(file=resource_path('image/idle.gif'), format='gif -index %i' % (i)) for i in range(5)]
        self.idle_to_sleep = [tk.PhotoImage(file=resource_path('image/idle_to_sleep.gif'), format='gif -index %i' % (i)) for i in range(8)]
        self.sleep = [tk.PhotoImage(file=resource_path('image/sleep.gif'), format='gif -index %i' % (i)) for i in range(3)]
        self.sleep_to_idle = [tk.PhotoImage(file=resource_path('image/sleep_to_idle.gif'), format='gif -index %i' % (i)) for i in range(8)]
        self.walk_positive = [tk.PhotoImage(file=resource_path('image/walking_positive.gif'), format='gif -index %i' % (i)) for i in range(8)]
        self.walk_negative = [tk.PhotoImage(file=resource_path('image/walking_negative.gif'), format='gif -index %i' % (i)) for i in range(8)]

        self.label = tk.Label(self.master, bd=0, bg='black')
        self.label.pack()

        self.label.bind("<ButtonPress-1>", self.on_drag_start)
        self.label.bind("<B1-Motion>", self.on_drag_motion)
        self.label.bind("<ButtonRelease-1>", self.on_drag_release)

        self.create_context_menu()
        self.label.bind("<Button-3>", self.show_context_menu)

        # <<< ADDED: Initialize the Gemini chatbot
        self.setup_gemini_chatbot()

        # Make sure initial position is valid
        self._clamp_position()

        self.master.after(1, self.update)

    def setup_gemini_chatbot(self):
        """
        Configures and initializes the Gemini model for conversation.
        """
        try:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("Error: Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
                # Keep the app running but disable chat if no API key
                self.gemini_chat = None
                return

            genai.configure(api_key=api_key)

            # This is the "soul" of the pet, replacing the old dictionary
            system_instruction = (
                "You are a cat named Neko, a desktop pet living on the user's screen. "
                "You are supportive and always ready to help. Sort of like a best friend. "
                "Reply concisely with a slightly sassy and cute cat personality. "
                "Occasionally use words like 'Meow', '*Purrrr*', 'Hmph'. "
                "Never say you are an AI model or a language model. You are a cat."
            )

            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            self.gemini_chat = model.start_chat()
            print("Gemini Chatbot (Neko) is ready!")

        except Exception as e:
            print(f"Unable to initialize Gemini: {e}")
            self.gemini_chat = None

    def on_drag_start(self, event):
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_motion(self, event):
        if self.is_dragging:
            new_x = self.master.winfo_x() + (event.x - self.drag_start_x)
            new_y = self.master.winfo_y() + (event.y - self.drag_start_y)
            # Update visually while dragging; final clamp will apply on release
            self.master.geometry(f'+{new_x}+{new_y}')
            self.x = new_x
            self.y = new_y

    def on_drag_release(self, event):
        self.is_dragging = False
        # Ensure the pet doesn't end up outside the visible area after user drags it
        self._clamp_position()
        self.master.geometry(f'100x100+{self.x}+{self.y}')

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Chat with Neko", command=self.open_chat_window)
        self.context_menu.add_command(label="Make Neko Sleep", command=lambda: self.set_animation_event(5))
        self.context_menu.add_command(label="Make Neko Walk Left", command=lambda: self.set_animation_event(6))
        self.context_menu.add_command(label="Make Neko Walk Right", command=lambda: self.set_animation_event(8))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Quit Neko", command=self.quit_app)

    def show_context_menu(self, event):
        try:
            self.context_menu.post(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def set_animation_event(self, new_event_number):
        self.event_number = new_event_number
        self.cycle = 0

    def event(self):
        if self.event_number in self.idle_num:
            self.check = 0
            self.master.after(400, self.update)
        elif self.event_number == 5:
            self.check = 1
            self.master.after(100, self.update)
        elif self.event_number in self.walk_left_num:
            self.check = 4
            self.master.after(100, self.update)
        elif self.event_number in self.walk_right_num:
            self.check = 5
            self.master.after(100, self.update)
        elif self.event_number in self.sleep_num:
            self.check = 2
            self.master.after(1000, self.update)
        elif self.event_number == 14:
            self.check = 3
            self.master.after(100, self.update)

    def gif_work(self, frames, first_num, last_num):
        if self.cycle < len(frames) - 1:
            self.cycle += 1
        else:
            self.cycle = 0
            self.event_number = random.randrange(first_num, last_num + 1, 1)
        return self.cycle, self.event_number

    def update(self):
        if not self.is_dragging:
            if self.check == 0:
                frame = self.idle[self.cycle]
                self.cycle, self.event_number = self.gif_work(self.idle, 1, 9)
            elif self.check == 1:
                frame = self.idle_to_sleep[self.cycle]
                self.cycle, self.event_number = self.gif_work(self.idle_to_sleep, 10, 10)
            elif self.check == 2:
                frame = self.sleep[self.cycle]
                self.cycle, self.event_number = self.gif_work(self.sleep, 10, 15)
            elif self.check == 3:
                frame = self.sleep_to_idle[self.cycle]
                self.cycle, self.event_number = self.gif_work(self.sleep_to_idle, 1, 1)
            elif self.check == 4:
                frame = self.walk_positive[self.cycle]
                self.cycle, self.event_number = self.gif_work(self.walk_positive, 1, 9)
                self.x -= 3
                # Clamp instead of raw wrap-around so Neko won't go out of screen
                self._clamp_position()
            elif self.check == 5:
                frame = self.walk_negative[self.cycle]
                self.cycle, self.event_number = self.gif_work(self.walk_negative, 1, 9)
                self.x += 3
                self._clamp_position()
        else:
            if self.check == 0: frame = self.idle[self.cycle]
            elif self.check == 1: frame = self.idle_to_sleep[self.cycle]
            elif self.check == 2: frame = self.sleep[self.cycle]
            elif self.check == 3: frame = self.sleep_to_idle[self.cycle]
            elif self.check == 4: frame = self.walk_positive[self.cycle]
            elif self.check == 5: frame = self.walk_negative[self.cycle]

        # Apply geometry (keep window size fixed to 100x100 as before)
        self.master.geometry(f'100x100+{self.x}+{self.y}')
        self.label.configure(image=frame)
        self.master.after(1, self.event)

    def open_chat_window(self):
        if self.chat_window is not None and self.chat_window.winfo_exists():
            self.chat_window.lift()
            return
        # Theme setup
        ctk.set_appearance_mode("dark")   # "dark", "light", "system"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

        # Tạo cửa sổ chat
        self.chat_window = ctk.CTkToplevel(self.master)
        self.chat_window.geometry("500x600")
        self.chat_window.title("Chat with Neko")
        self.chat_window.attributes("-topmost", True)

        # Khung chat hiển thị tin nhắn
        self.chat_display = ctk.CTkTextbox(
            self.chat_window,
            wrap="word",
            width=480,
            height=500,
            font=("Segoe UI", 12)
        )
        self.chat_display.configure(state="disabled")
        self.chat_display.pack(padx=10, pady=10, fill="both", expand=True)

        # Khung nhập tin nhắn + nút send
        input_frame = ctk.CTkFrame(self.chat_window)
        input_frame.pack(fill="x", padx=10, pady=10)

        self.user_input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message...",
            width=350
        )
        self.user_input_entry.pack(side="left", padx=(0,10), expand=True, fill="x")
        self.user_input_entry.bind("<Return>", lambda event=None: self.send_chat_message())

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_chat_message
        )
        self.send_button.pack(side="right")


    def send_chat_message(self):
        """Handles sending the user message to Gemini in a separate thread."""
        user_message = self.user_input_entry.get().strip()
        if not user_message:
            return

        # Hiển thị tin nhắn user
        self._insert_chat_message(f"You: {user_message}\n")
        self.user_input_entry.delete(0, tk.END)

        # Tạm disable input
        self.user_input_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self._insert_chat_message("Neko is typing...\n\n")

        # Tạo thread để gọi API
        thread = threading.Thread(target=self._get_gemini_response, args=(user_message,))
        thread.daemon = True
        thread.start()

    def _get_gemini_response(self, user_message):
        """Gọi Gemini API trong thread riêng."""
        try:
            if not self.gemini_chat:
                raise RuntimeError("Gemini is not initialized.")
            response = self.gemini_chat.send_message(user_message)
            neko_response = response.text
        except Exception as e:
            neko_response = f"Meow... (Error: {e})"

        # Gửi kết quả về main thread
        self.master.after(0, self._update_chat_with_response, neko_response)

    def _update_chat_with_response(self, neko_response):
        """Cập nhật chat box với câu trả lời từ Neko."""
        # Xoá dòng "Neko is typing..."
        self.chat_display.configure(state="normal")
        content = self.chat_display.get("1.0", "end")
        if "Neko is typing..." in content:
            new_content = content.replace("Neko is typing...\n\n", "")
            self.chat_display.delete("1.0", "end")
            self.chat_display.insert("1.0", new_content)
        self.chat_display.configure(state="disabled")

        # Thêm câu trả lời thật
        self._insert_chat_message(f"Neko: {neko_response}\n\n")

        # Bật lại input
        self.user_input_entry.configure(state="normal")
        self.send_button.configure(state="normal")
        self.user_input_entry.focus_set()

    def _insert_chat_message(self, message: str):
        """Thêm tin nhắn vào chat box."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", message)
        self.chat_display.see("end")  # luôn cuộn xuống cuối
        self.chat_display.configure(state="disabled")

    def close_chat_window(self, win):
        win.destroy()
        self.chat_window = None

    def quit_app(self):
        self.master.destroy()

    # ------------------ New helper methods for clamping & sizes ------------------
    def _get_screen_size(self):
        self.master.update_idletasks()
        return self.master.winfo_screenwidth(), self.master.winfo_screenheight()

    def _get_pet_size(self):
        """Try to determine the pet window / label size; fall back to 100x100 if unknown."""
        self.master.update_idletasks()
        pet_w, pet_h = 100, 100
        try:
            mw = self.master.winfo_width()
            mh = self.master.winfo_height()
            if mw > 0:
                pet_w = mw
            if mh > 0:
                pet_h = mh
            lw = self.label.winfo_width()
            lh = self.label.winfo_height()
            if lw > 0:
                pet_w = lw
            if lh > 0:
                pet_h = lh
        except Exception:
            pass
        return pet_w, pet_h

    def _clamp_position(self):
        """Clamp self.x/self.y so the pet stays inside the visible screen area."""
        screen_w, screen_h = self._get_screen_size()
        pet_w, pet_h = self._get_pet_size()

        min_x, max_x = 0, max(0, screen_w - pet_w)
        min_y, max_y = 0, max(0, screen_h - pet_h)

        self.x = max(min_x, min(self.x, max_x))
        self.y = max(min_y, min(self.y, max_y))


# --- Main execution block ---
if __name__ == "__main__":
    # Optional: make the process DPI aware on Windows so winfo_screenwidth/height return real pixels
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

    root = tk.Tk()
    app = DesktopPetApp(root)
    root.mainloop()
