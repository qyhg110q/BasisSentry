from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import AsyncIterator, Callable

import websockets


@dataclass
class SpotStreamMessage:
    stream: str
    data: dict


class SpotWsClient:
    def __init__(
        self,
        base_url: str,
        symbols: list[str],
        max_streams_per_conn: int,
        backoff_min: int,
        backoff_max: int,
        proxy_url: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.symbols = symbols
        self.max_streams_per_conn = max_streams_per_conn
        self.backoff_min = backoff_min
        self.backoff_max = backoff_max
        self.proxy_url = proxy_url
        self.logger = logging.getLogger("spot_ws")

    def _build_streams(self) -> list[str]:
        streams: list[str] = []
        for symbol in self.symbols:
            streams.append(f"{symbol}@bookTicker")
            streams.append(f"{symbol}@depth20@100ms")
            streams.append(f"{symbol}@aggTrade")
        return streams

    def _chunks(self, streams: list[str]) -> list[list[str]]:
        return [streams[i : i + self.max_streams_per_conn] for i in range(0, len(streams), self.max_streams_per_conn)]

    async def _connect(self, streams: list[str], handler: Callable[[SpotStreamMessage], None]) -> None:
        stream_path = "/stream?streams=" + "/".join(streams)
        url = f"{self.base_url}{stream_path}"
        rotate_after = 24 * 60 * 60
        backoff = self.backoff_min
        while True:
            try:
                async with websockets.connect(url, ping_interval=None, proxy=self.proxy_url) as ws:
                    self.logger.info("spot ws connected: %s", url)
                    rotate_task = asyncio.create_task(asyncio.sleep(rotate_after))
                    while True:
                        done, _ = await asyncio.wait(
                            {asyncio.create_task(ws.recv()), rotate_task},
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                        if rotate_task in done:
                            self.logger.info("spot ws rotate")
                            break
                        message = done.pop().result()
                        payload = json.loads(message)
                        if "stream" in payload and "data" in payload:
                            handler(SpotStreamMessage(stream=payload["stream"], data=payload["data"]))
                    rotate_task.cancel()
            except Exception as exc:
                self.logger.warning("spot ws error: %s", exc)
            await asyncio.sleep(backoff)
            backoff = min(self.backoff_max, backoff * 2)

    async def run(self, handler: Callable[[SpotStreamMessage], None]) -> None:
        streams = self._build_streams()
        tasks = []
        for chunk in self._chunks(streams):
            tasks.append(asyncio.create_task(self._connect(chunk, handler)))
        await asyncio.gather(*tasks)
