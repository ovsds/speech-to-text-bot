import dataclasses
import logging

import aiogram
import aiogram.filters as aiogram_filters
import aiogram.types as aiogram_types

default_logger = logging.getLogger("aiogram.filters")


@dataclasses.dataclass(frozen=True)
class ContentTypeMessageFilter(aiogram_filters.Filter):
    content_type: aiogram_types.ContentType
    logger: logging.Logger = default_logger

    async def __call__(self, message: aiogram_types.Message, bot: aiogram.Bot) -> bool:
        if message.content_type != self.content_type:
            self.logger.debug("Message content type does not match(%s != %s)", message.content_type, self.content_type)
            return False

        self.logger.debug("Message content type matches(%s == %s)", message.content_type, self.content_type)
        return True


__all__ = [
    "ContentTypeMessageFilter",
]
