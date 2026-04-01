from __future__ import annotations

import argparse
import sys

from PyQt5.QtWidgets import QApplication

from .application import ControllerMapperApplication


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zero2-input-inspector")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Start hidden and keep the mapper running from the tray.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("zero2-input-inspector")
    app.setOrganizationName("zero2")
    app.setQuitOnLastWindowClosed(False)

    controller_app = ControllerMapperApplication(app, start_hidden=args.background)
    controller_app.start()

    return app.exec_()
