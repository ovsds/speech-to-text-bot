import dataclasses
import typing

import aiogram
import aiogram.filters as aiogram_filters
import aiogram.types as aiogram_types

import lib.utils.aiogram as aiogram_utils

HELP_MESSAGE = (
    "This bot is a simple bot that converts voice/video messages to text. "
    "\n\n"
    "In case of any issues check the repo:\n"
    "https://github.com/ovsds/speech-to-text-bot"
)


@dataclasses.dataclass(frozen=True)
class HelpCommandHandler:
    async def process(self, message: aiogram_types.Message):
        await message.answer(
            aiogram_utils.escape_symbols(HELP_MESSAGE, ".-"),
            parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
        )

    @property
    def bot_commands(self) -> typing.Sequence[aiogram_types.BotCommand]:
        return [
            aiogram_types.BotCommand(command="help", description="Show help message"),
            aiogram_types.BotCommand(command="start", description="Start the bot"),
        ]

    @property
    def filters(self) -> typing.Sequence[aiogram_filters.Filter]:
        return [aiogram_filters.Command(commands=self.bot_commands)]


__all__ = [
    "HelpCommandHandler",
]
