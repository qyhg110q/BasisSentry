from __future__ import annotations

import logging
import sys


class AlertManager:
    def __init__(self) -> None:
        self.logger = logging.getLogger("alerts")

    def notify(self, message: str) -> None:
        self.logger.warning(message)
        sys.stdout.write("\a")
        sys.stdout.flush()
