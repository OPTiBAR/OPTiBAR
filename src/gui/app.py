import multiprocessing

from gui.view.root import Root
from gui.control.controller import Controller


def main():
    # required for engine processes in a frozen (PyInstaller) build; no-op otherwise
    multiprocessing.freeze_support()
    root = Root()
    Controller(root)
    root.mainloop()


if __name__ == '__main__':
    main()
