import asyncio
import sys
from types import SimpleNamespace

from ymrpc.discord_rpc import DiscordRPC
from ymrpc.models import PlaybackState, Track


def test_rpc_uses_async_client_inside_running_event_loop(monkeypatch):
    calls: list[str] = []

    class FakeAioPresence:
        def __init__(self, client_id):
            calls.append(f"init:{client_id}")

        async def connect(self):
            calls.append("connect")

        async def update(self, **payload):
            calls.append(f"update:{payload['details']}")

        async def clear(self):
            calls.append("clear")

    monkeypatch.setitem(sys.modules, "pypresence", SimpleNamespace(AioPresence=FakeAioPresence))

    async def scenario():
        rpc = DiscordRPC("12345678901234567")
        track = Track(title="Song", artist="Artist", state=PlaybackState.PLAYING)
        await rpc.update(track)
        await rpc.clear()
        await rpc.close()

    asyncio.run(scenario())
    assert calls == [
        "init:12345678901234567",
        "connect",
        "update:Song",
        "clear",
    ]
