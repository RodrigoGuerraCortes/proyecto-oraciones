# generator/v2/video/background_selector/filesystem.py

import os
import random
from .base import BackgroundSelector


class FilesystemBackgroundSelector(BackgroundSelector):

    def __init__(self, base_path: str, fallback: str = "default"):
        self.base_path = base_path
        self.fallback = fallback

    def elegir(self, *, text: str, title: str) -> str:
        text_l = f"{title} {text}".lower()

        rules = {
            "angel": ["angel", "ángel"],
            "jesus": ["jesus", "jesús", "cristo"],
            "maria": ["maria", "maría", "virgen"],
            "cruz": ["cruz"],
            "espiritu_santo": ["espiritu", "espíritu"],
            "naturaleza": ["paz", "calma", "descanso"],
        }

        for folder, keywords in rules.items():
            if any(k in text_l for k in keywords):
                return self._pick(folder)

        return self._pick(self.fallback)

    def _pick(self, folder: str) -> str:
        path = os.path.join(self.base_path, folder)
        imgs = os.listdir(path)
        return os.path.join(path, random.choice(imgs))
