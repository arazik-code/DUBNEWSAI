from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable


class CircuitBreakerOpenError(RuntimeError):
    pass


@dataclass(slots=True)
class ProviderHealthState:
    failures: int = 0
    successes: int = 0
    consecutive_failures: int = 0
    last_failure_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None
    state: str = "closed"
    opened_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def reliability(self) -> float:
        total = self.failures + self.successes
        if total == 0:
            return 100.0
        return round((self.successes / total) * 100, 2)


class ProviderHealthMonitor:
    def __init__(self, *, failure_threshold: int = 3, recovery_timeout_seconds: int = 300) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self._states: dict[str, ProviderHealthState] = {}

    def _state(self, provider_name: str) -> ProviderHealthState:
        return self._states.setdefault(provider_name, ProviderHealthState())

    def snapshot(self, provider_name: str) -> ProviderHealthState:
        state = self._state(provider_name)
        self._evaluate_state(provider_name, state)
        return state

    def get_health_report(self) -> dict[str, dict[str, Any]]:
        report: dict[str, dict[str, Any]] = {}
        for provider_name in sorted(self._states):
            state = self.snapshot(provider_name)
            report[provider_name] = {
                "health_score": state.reliability,
                "circuit_state": state.state,
                "last_error": state.last_error,
                "last_success_at": state.last_success_at.isoformat() if state.last_success_at else None,
                "last_failure_at": state.last_failure_at.isoformat() if state.last_failure_at else None,
            }
        return report

    def reset(self, provider_name: str) -> ProviderHealthState:
        state = self._state(provider_name)
        state.failures = 0
        state.successes = 0
        state.consecutive_failures = 0
        state.last_failure_at = None
        state.last_success_at = None
        state.last_error = None
        state.state = "closed"
        state.opened_at = None
        state.metadata.clear()
        return state

    def is_open(self, provider_name: str) -> bool:
        state = self._state(provider_name)
        self._evaluate_state(provider_name, state)
        return state.state == "open"

    def _evaluate_state(self, provider_name: str, state: ProviderHealthState) -> None:
        if state.state != "open" or state.opened_at is None:
            return
        if datetime.now(timezone.utc) - state.opened_at >= self.recovery_timeout:
            state.state = "half_open"
            state.opened_at = None
            state.metadata["transition"] = "recovery_window_elapsed"

    def record_success(self, provider_name: str) -> ProviderHealthState:
        state = self._state(provider_name)
        state.successes += 1
        state.consecutive_failures = 0
        state.last_success_at = datetime.now(timezone.utc)
        state.last_error = None
        state.state = "closed"
        state.opened_at = None
        return state

    def record_failure(self, provider_name: str, error: Exception) -> ProviderHealthState:
        state = self._state(provider_name)
        state.failures += 1
        state.consecutive_failures += 1
        state.last_failure_at = datetime.now(timezone.utc)
        state.last_error = str(error)
        if state.consecutive_failures >= self.failure_threshold:
            state.state = "open"
            state.opened_at = datetime.now(timezone.utc)
        return state

    async def call_provider(
        self,
        provider_name: str,
        operation: Callable[..., Awaitable[Any] | Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if self.is_open(provider_name):
            raise CircuitBreakerOpenError(f"Circuit breaker open for {provider_name}")

        try:
            result = operation(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            self.record_success(provider_name)
            return result
        except Exception as exc:
            self.record_failure(provider_name, exc)
            raise

    async def warmup(self, provider_name: str, delay_seconds: float = 0.0) -> None:
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        self._evaluate_state(provider_name, self._state(provider_name))


provider_health = ProviderHealthMonitor()
