import multiprocessing

from optibar.gui.view.root import Root
from optibar.gui.control.controller import Controller


def main():
    # required for engine processes in a frozen (PyInstaller) build; no-op otherwise
    multiprocessing.freeze_support()
    root = Root()
    Controller(root)
    root.mainloop()


if __name__ == '__main__':
    main()
