from __future__ import annotations

import asyncio
from dataclasses import dataclass

import aiohttp

from app.config import AutoFilters


SPOT_EXCHANGE_INFO = "https://api.binance.com/api/v3/exchangeInfo"
FUTURES_EXCHANGE_INFO = "https://fapi.binance.com/fapi/v1/exchangeInfo"


@dataclass
class Universe:
    symbols: list[str]


async def fetch_exchange_info(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url, timeout=20) as resp:
        resp.raise_for_status()
        return await resp.json()


def _filter_spot_symbols(payload: dict, quote: str) -> set[str]:
    results = set()
    for symbol in payload.get("symbols", []):
        if symbol.get("status") != "TRADING":
            continue
        if symbol.get("quoteAsset") != quote:
            continue
        results.add(symbol.get("symbol", "").lower())
    return results


def _filter_futures_symbols(payload: dict, contract_type: str) -> set[str]:
    results = set()
    for symbol in payload.get("symbols", []):
        if symbol.get("contractType") != contract_type:
            continue
        if symbol.get("status") not in {"TRADING", "PENDING_TRADING"}:
            continue
        results.add(symbol.get("symbol", "").lower())
    return results


async def load_universe(filters: AutoFilters) -> Universe:
    async with aiohttp.ClientSession() as session:
        spot_payload, futures_payload = await asyncio.gather(
            fetch_exchange_info(session, SPOT_EXCHANGE_INFO),
            fetch_exchange_info(session, FUTURES_EXCHANGE_INFO),
        )
    spot_symbols = _filter_spot_symbols(spot_payload, filters.quote)
    futures_symbols = _filter_futures_symbols(futures_payload, filters.futures_contract_type)
    intersection = sorted(spot_symbols & futures_symbols)
    return Universe(symbols=intersection[: filters.max_symbols])
