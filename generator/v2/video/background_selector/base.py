# generator/v2/video/background_selector/base.py

from abc import ABC, abstractmethod


class BackgroundSelector(ABC):

    @abstractmethod
    def elegir(
        self,
        *,
        text: str,
        title: str,
        format_code: str,
        channel_code: str,
    ) -> str:
        """
        Retorna path absoluto a imagen de fondo.
        """
        raise NotImplementedError
