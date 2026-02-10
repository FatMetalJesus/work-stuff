from __future__ import annotations

import tkinter as tk

from .app import OmniRecoverStudioApp


def main() -> None:
    root = tk.Tk()
    OmniRecoverStudioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
