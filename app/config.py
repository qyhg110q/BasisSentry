from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class AutoFilters:
    quote: str = "USDT"
    futures_contract_type: str = "PERPETUAL"
    max_symbols: int = 300


@dataclass
class SymbolsConfig:
    mode: Literal["auto", "manual"] = "auto"
    manual_list: list[str] = field(default_factory=list)
    auto_filters: AutoFilters = field(default_factory=AutoFilters)


@dataclass
class ReconnectBackoff:
    min: int = 1
    max: int = 60


@dataclass
class WsConfig:
    spot_base: str = "wss://stream.binance.com:9443"
    futures_base: str = "wss://fstream.binance.com"
    max_streams_per_conn: int = 800
    reconnect_backoff: ReconnectBackoff = field(default_factory=ReconnectBackoff)


@dataclass
class RestConfig:
    spot_endpoints: list[str] = field(
        default_factory=lambda: [
            "https://api.binance.com/api/v3/exchangeInfo",
            "https://api1.binance.com/api/v3/exchangeInfo",
            "https://api2.binance.com/api/v3/exchangeInfo",
            "https://api3.binance.com/api/v3/exchangeInfo",
        ]
    )
    futures_endpoints: list[str] = field(
        default_factory=lambda: [
            "https://fapi.binance.com/fapi/v1/exchangeInfo",
            "https://fapi1.binance.com/fapi/v1/exchangeInfo",
            "https://fapi2.binance.com/fapi/v1/exchangeInfo",
            "https://fapi3.binance.com/fapi/v1/exchangeInfo",
        ]
    )
    timeout_seconds: int = 10
    max_retries: int = 3


@dataclass
class BasisConfig:
    window_seconds: int = 300
    basis_abs_threshold: float = 0.02
    z_threshold: float = 5.0
    min_duration_s: int = 10
    sigma_floor_bps: float = 1.0


@dataclass
class TradeConfirmConfig:
    use_aggTrade: bool = True
    trade_window_s: int = 2
    trade_price_bps: float = 5
    trade_explain_ratio: float = 0.2


@dataclass
class WallConfig:
    enabled: bool = True
    levels: int = 20
    speed: str = "100ms"
    hard_min_wall_usdt: float = 200000
    k_median: float = 8
    share_threshold: float = 0.25
    range_bps: float = 30
    trade_confirm: TradeConfirmConfig = field(default_factory=TradeConfirmConfig)


@dataclass
class EventPackConfig:
    pre_seconds: int = 120
    post_seconds: int = 180


@dataclass
class OutputConfig:
    data_dir: str = "./data"
    log_level: str = "INFO"


@dataclass
class UiConfig:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass
class AppConfig:
    symbols: SymbolsConfig = field(default_factory=SymbolsConfig)
    rest: RestConfig = field(default_factory=RestConfig)
    ws: WsConfig = field(default_factory=WsConfig)
    basis: BasisConfig = field(default_factory=BasisConfig)
    wall: WallConfig = field(default_factory=WallConfig)
    event_pack: EventPackConfig = field(default_factory=EventPackConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    ui: UiConfig = field(default_factory=UiConfig)


def load_config(path: str | Path) -> AppConfig:
    import yaml

    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text()) or {}

    symbols_raw = raw.get("symbols", {})
    auto_filters_raw = symbols_raw.get("auto_filters", {})
    ws_raw = raw.get("ws", {})
    backoff_raw = ws_raw.get("reconnect_backoff", {})
    rest_raw = raw.get("rest", {})
    basis_raw = raw.get("basis", {})
    wall_raw = raw.get("wall", {})
    trade_confirm_raw = wall_raw.get("trade_confirm", {})
    event_pack_raw = raw.get("event_pack", {})
    output_raw = raw.get("output", {})
    ui_raw = raw.get("ui", {})

    return AppConfig(
        symbols=SymbolsConfig(
            mode=symbols_raw.get("mode", "auto"),
            manual_list=symbols_raw.get("manual_list", []),
            auto_filters=AutoFilters(
                quote=auto_filters_raw.get("quote", "USDT"),
                futures_contract_type=auto_filters_raw.get("futures_contract_type", "PERPETUAL"),
                max_symbols=auto_filters_raw.get("max_symbols", 300),
            ),
        ),
        rest=RestConfig(
            spot_endpoints=rest_raw.get(
                "spot_endpoints",
                [
                    "https://api.binance.com/api/v3/exchangeInfo",
                    "https://api1.binance.com/api/v3/exchangeInfo",
                    "https://api2.binance.com/api/v3/exchangeInfo",
                    "https://api3.binance.com/api/v3/exchangeInfo",
                ],
            ),
            futures_endpoints=rest_raw.get(
                "futures_endpoints",
                [
                    "https://fapi.binance.com/fapi/v1/exchangeInfo",
                    "https://fapi1.binance.com/fapi/v1/exchangeInfo",
                    "https://fapi2.binance.com/fapi/v1/exchangeInfo",
                    "https://fapi3.binance.com/fapi/v1/exchangeInfo",
                ],
            ),
            timeout_seconds=rest_raw.get("timeout_seconds", 10),
            max_retries=rest_raw.get("max_retries", 3),
        ),
        ws=WsConfig(
            spot_base=ws_raw.get("spot_base", "wss://stream.binance.com:9443"),
            futures_base=ws_raw.get("futures_base", "wss://fstream.binance.com"),
            max_streams_per_conn=ws_raw.get("max_streams_per_conn", 800),
            reconnect_backoff=ReconnectBackoff(
                min=backoff_raw.get("min", 1),
                max=backoff_raw.get("max", 60),
            ),
        ),
        basis=BasisConfig(
            window_seconds=basis_raw.get("window_seconds", 300),
            basis_abs_threshold=basis_raw.get("basis_abs_threshold", 0.02),
            z_threshold=basis_raw.get("z_threshold", 5.0),
            min_duration_s=basis_raw.get("min_duration_s", 10),
            sigma_floor_bps=basis_raw.get("sigma_floor_bps", 1.0),
        ),
        wall=WallConfig(
            enabled=wall_raw.get("enabled", True),
            levels=wall_raw.get("levels", 20),
            speed=wall_raw.get("speed", "100ms"),
            hard_min_wall_usdt=wall_raw.get("hard_min_wall_usdt", 200000),
            k_median=wall_raw.get("k_median", 8),
            share_threshold=wall_raw.get("share_threshold", 0.25),
            range_bps=wall_raw.get("range_bps", 30),
            trade_confirm=TradeConfirmConfig(
                use_aggTrade=trade_confirm_raw.get("use_aggTrade", True),
                trade_window_s=trade_confirm_raw.get("trade_window_s", 2),
                trade_price_bps=trade_confirm_raw.get("trade_price_bps", 5),
                trade_explain_ratio=trade_confirm_raw.get("trade_explain_ratio", 0.2),
            ),
        ),
        event_pack=EventPackConfig(
            pre_seconds=event_pack_raw.get("pre_seconds", 120),
            post_seconds=event_pack_raw.get("post_seconds", 180),
        ),
        output=OutputConfig(
            data_dir=output_raw.get("data_dir", "./data"),
            log_level=output_raw.get("log_level", "INFO"),
        ),
        ui=UiConfig(
            enabled=ui_raw.get("enabled", True),
            host=ui_raw.get("host", "127.0.0.1"),
            port=ui_raw.get("port", 8000),
        ),
    )
