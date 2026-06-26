import customtkinter as ctk

from app import App


def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
