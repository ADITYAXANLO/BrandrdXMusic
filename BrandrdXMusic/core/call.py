import asyncio
from typing import Union

from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    MediumQualityVideo,
)
from pytgcalls.types.stream import StreamAudioEnded

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import (
    get_assistant,
    get_assistant_chat,
    get_client,
    get_lang,
    get_loop,
    get_served_chats,
    get_video_limit,
    is_active_chat,
    is_music_playing,
    remove_active_chat,
    set_loop,
)
from BrandrdXMusic.utils.exceptions import AssistantErr
from BrandrdXMusic.utils.formatters import seconds_to_min
from config import LOG_GROUP_ID


class Call:
    def __init__(self):
        self.clients = {}
        self.streams = {}
        self.video_calls = {}
        self.active_chats = []
        self.playlist = {}

        self.userbot1 = None
        self.userbot2 = None
        self.userbot3 = None
        self.userbot4 = None
        self.userbot5 = None

        self.calls = {}
        self.call_clients = {}

    async def get_call(self, client):
        if client in self.calls:
            return self.calls[client]

        call = PyTgCalls(client)
        self.calls[client] = call

        return call

    async def start(self):
        clients = [
            self.userbot1,
            self.userbot2,
            self.userbot3,
            self.userbot4,
            self.userbot5,
        ]

        for client in clients:
            if client is None:
                continue

            try:
                await client.start()
            except Exception:
                pass

            try:
                self.call_clients[client] = PyTgCalls(client)
                await self.call_clients[client].start()
            except Exception:
                pass

    async def join_call(
        self,
        chat_id: int,
        client: Client,
        audio: Union[str, AudioPiped],
        video: Union[str, AudioVideoPiped] = None,
    ):
        if client not in self.call_clients:
            self.call_clients[client] = PyTgCalls(client)

        assistant = self.call_clients[client]

        if video:
            stream = AudioVideoPiped(
                video,
                HighQualityAudio(),
                MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(
                audio,
                HighQualityAudio(),
            )

        try:
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )

        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])

        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])

        except Exception as e:
            raise AssistantErr(
                f"Failed to join voice chat:\n`{e}`"
            )

        self.active_chats.append(chat_id)

        return True

    async def leave_call(self, chat_id: int):
        for client, assistant in self.call_clients.items():
            try:
                await assistant.leave_group_call(chat_id)
            except Exception:
                pass

        if chat_id in self.active_chats:
            self.active_chats.remove(chat_id)

        self.streams.pop(chat_id, None)
        self.video_calls.pop(chat_id, None)

        try:
            await remove_active_chat(chat_id)
        except Exception:
            pass

        return True

    async def pause_stream(self, chat_id: int):
        for assistant in self.call_clients.values():
            try:
                await assistant.pause_stream(chat_id)
            except Exception:
                pass

        return True

    async def resume_stream(self, chat_id: int):
        for assistant in self.call_clients.values():
            try:
                await assistant.resume_stream(chat_id)
            except Exception:
                pass

        return True

    async def change_volume(self, chat_id: int, volume: int):
        for assistant in self.call_clients.values():
            try:
                await assistant.change_volume_call(
                    chat_id,
                    volume,
                )
            except Exception:
                pass

        return True

    async def mute_stream(self, chat_id: int):
        for assistant in self.call_clients.values():
            try:
                await assistant.mute_stream(chat_id)
            except Exception:
                pass

        return True

    async def unmute_stream(self, chat_id: int):
        for assistant in self.call_clients.values():
            try:
                await assistant.unmute_stream(chat_id)
            except Exception:
                pass

        return True

    async def update_stream(
        self,
        chat_id: int,
        stream: Union[AudioPiped, AudioVideoPiped],
    ):
        for assistant in self.call_clients.values():
            try:
                await assistant.change_stream(
                    chat_id,
                    stream,
                )
                return True
            except Exception:
                continue

        return False

    async def force_stop(self, chat_id: int):
        try:
            await self.leave_call(chat_id)
        except Exception:
            pass

        self.playlist.pop(chat_id, None)
        self.streams.pop(chat_id, None)
        self.video_calls.pop(chat_id, None)

        return True

    async def skip(self, chat_id: int, stream):
        return await self.update_stream(
            chat_id,
            stream,
        )

    async def play_next(
        self,
        chat_id: int,
        stream,
    ):
        if chat_id not in self.active_chats:
            return False

        return await self.update_stream(
            chat_id,
            stream,
        )

    async def is_active(self, chat_id: int):
        try:
            return await is_active_chat(chat_id)
        except Exception:
            return chat_id in self.active_chats

    async def is_playing(self, chat_id: int):
        try:
            return await is_music_playing(chat_id)
        except Exception:
            return False

    async def get_stream(self, chat_id: int):
        return self.streams.get(chat_id)

    async def set_stream(self, chat_id: int, stream):
        self.streams[chat_id] = stream
        return True

    async def get_video_call(self, chat_id: int):
        return self.video_calls.get(chat_id)

    async def set_video_call(self, chat_id: int, value):
        self.video_calls[chat_id] = value
        return True

    async def get_playlist(self, chat_id: int):
        return self.playlist.get(chat_id, [])

    async def set_playlist(self, chat_id: int, playlist):
        self.playlist[chat_id] = playlist
        return True

    async def clear_playlist(self, chat_id: int):
        self.playlist.pop(chat_id, None)
        return True

    async def get_call_client(self, client):
        return self.call_clients.get(client)

    async def cleanup(self):
        for chat_id in list(self.active_chats):
            try:
                await self.leave_call(chat_id)
            except Exception:
                pass

        for client, assistant in list(self.call_clients.items()):
            try:
                await assistant.stop()
            except Exception:
                pass

        self.call_clients.clear()
        self.active_chats.clear()
        self.streams.clear()
        self.video_calls.clear()
        self.playlist.clear()


Hotty = Call()
