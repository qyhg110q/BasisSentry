from __future__ import annotations

import asyncio
from dataclasses import dataclass

import aiohttp

from app.config import AutoFilters, RestConfig


@dataclass
class Universe:
    symbols: list[str]


async def fetch_exchange_info(
    session: aiohttp.ClientSession,
    endpoints: list[str],
    timeout_seconds: int,
    max_retries: int,
) -> dict:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        for url in endpoints:
            try:
                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with session.get(url, timeout=timeout) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = exc
                await asyncio.sleep(min(2**attempt, 5))
    message = f"failed to fetch exchange info from {endpoints}"
    raise RuntimeError(message) from last_error


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


async def load_universe(filters: AutoFilters, rest: RestConfig) -> Universe:
    async with aiohttp.ClientSession(trust_env=True) as session:
        spot_payload, futures_payload = await asyncio.gather(
            fetch_exchange_info(
                session,
                rest.spot_endpoints,
                rest.timeout_seconds,
                rest.max_retries,
            ),
            fetch_exchange_info(
                session,
                rest.futures_endpoints,
                rest.timeout_seconds,
                rest.max_retries,
            ),
        )
    spot_symbols = _filter_spot_symbols(spot_payload, filters.quote)
    futures_symbols = _filter_futures_symbols(futures_payload, filters.futures_contract_type)
    intersection = sorted(spot_symbols & futures_symbols)
    return Universe(symbols=intersection[: filters.max_symbols])
