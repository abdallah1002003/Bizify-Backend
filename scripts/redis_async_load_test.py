#!/usr/bin/env python3
"""Async Redis load profiler for Bizify.

This script stress-tests Redis using asyncio and reports:
- Throughput (ops/sec)
- Error rate
- Latency p50 / p95 / p99 (milliseconds)
"""

from __future__ import annotations

import argparse
import asyncio
import random
import time
from dataclasses import dataclass
from typing import Sequence

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError


@dataclass(frozen=True)
class LoadConfig:
    host: str
    port: int
    db: int
    password: str | None
    concurrency: int
    operations: int
    read_ratio: float
    keyspace: int
    value_size: int
    ttl_seconds: int
    warmup_operations: int


@dataclass(frozen=True)
class LoadResult:
    elapsed_seconds: float
    total_operations: int
    errors: int
    latencies_ms: list[float]

    @property
    def throughput(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0
        return self.total_operations / self.elapsed_seconds

    @property
    def error_rate(self) -> float:
        if self.total_operations <= 0:
            return 0.0
        return (self.errors / self.total_operations) * 100.0


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0

    if percentile <= 0:
        return min(values)
    if percentile >= 100:
        return max(values)

    sorted_vals = sorted(values)
    position = (len(sorted_vals) - 1) * (percentile / 100.0)
    low = int(position)
    high = min(low + 1, len(sorted_vals) - 1)
    fraction = position - low
    return sorted_vals[low] + (sorted_vals[high] - sorted_vals[low]) * fraction


def _make_value(size: int) -> bytes:
    return b"x" * size


async def _seed_keys(redis: Redis, keyspace: int, payload: bytes, ttl_seconds: int) -> None:
    for idx in range(keyspace):
        await redis.set(f"perf:key:{idx}", payload, ex=ttl_seconds)


async def _run_worker(
    redis: Redis,
    *,
    worker_index: int,
    operation_count: int,
    read_ratio: float,
    keyspace: int,
    payload: bytes,
    ttl_seconds: int,
) -> tuple[list[float], int]:
    latencies: list[float] = []
    errors = 0

    for op_idx in range(operation_count):
        key_index = random.randint(0, keyspace - 1)
        key = f"perf:key:{key_index}"
        is_read = random.random() <= read_ratio

        started = time.perf_counter()
        try:
            if is_read:
                await redis.get(key)
            else:
                await redis.set(
                    key,
                    payload,
                    ex=ttl_seconds,
                )
        except Exception:
            errors += 1
        finally:
            latencies.append((time.perf_counter() - started) * 1000.0)

        if op_idx % 5000 == 0 and op_idx > 0:
            # Keep keys hot for mixed workloads by occasionally writing unique slots.
            write_key = f"perf:worker:{worker_index}:{op_idx}"
            try:
                await redis.set(write_key, payload, ex=ttl_seconds)
            except Exception:
                errors += 1

    return latencies, errors


async def run_load_profile(config: LoadConfig) -> LoadResult:
    redis = Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        decode_responses=False,
        socket_timeout=5,
        socket_connect_timeout=5,
    )

    try:
        pong = await redis.ping()
        if not pong:
            raise RuntimeError("Redis ping failed")

        payload = _make_value(config.value_size)

        print(
            f"Warmup: {config.warmup_operations} ops | "
            f"concurrency={config.concurrency} keyspace={config.keyspace}"
        )
        await _seed_keys(redis, config.keyspace, payload, config.ttl_seconds)

        if config.warmup_operations > 0:
            warmup_per_worker = max(1, config.warmup_operations // config.concurrency)
            await asyncio.gather(
                *[
                    _run_worker(
                        redis,
                        worker_index=i,
                        operation_count=warmup_per_worker,
                        read_ratio=config.read_ratio,
                        keyspace=config.keyspace,
                        payload=payload,
                        ttl_seconds=config.ttl_seconds,
                    )
                    for i in range(config.concurrency)
                ]
            )

        ops_per_worker = max(1, config.operations // config.concurrency)
        planned_ops = ops_per_worker * config.concurrency
        print(
            f"Benchmark: {planned_ops} ops | read_ratio={config.read_ratio:.2f} "
            f"value_size={config.value_size} bytes"
        )

        started = time.perf_counter()
        worker_results = await asyncio.gather(
            *[
                _run_worker(
                    redis,
                    worker_index=i,
                    operation_count=ops_per_worker,
                    read_ratio=config.read_ratio,
                    keyspace=config.keyspace,
                    payload=payload,
                    ttl_seconds=config.ttl_seconds,
                )
                for i in range(config.concurrency)
            ]
        )
        elapsed = time.perf_counter() - started

        all_latencies: list[float] = []
        total_errors = 0
        for latencies, errors in worker_results:
            all_latencies.extend(latencies)
            total_errors += errors

        return LoadResult(
            elapsed_seconds=elapsed,
            total_operations=planned_ops,
            errors=total_errors,
            latencies_ms=all_latencies,
        )
    finally:
        await redis.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Async Redis load profiler")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=6379)
    parser.add_argument("--db", type=int, default=0)
    parser.add_argument("--password", default=None)
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--operations", type=int, default=50000)
    parser.add_argument("--read-ratio", type=float, default=0.8)
    parser.add_argument("--keyspace", type=int, default=10000)
    parser.add_argument("--value-size", type=int, default=512)
    parser.add_argument("--ttl-seconds", type=int, default=300)
    parser.add_argument("--warmup-operations", type=int, default=5000)
    return parser


async def _main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.concurrency <= 0:
        raise ValueError("--concurrency must be > 0")
    if args.operations <= 0:
        raise ValueError("--operations must be > 0")
    if not 0.0 <= args.read_ratio <= 1.0:
        raise ValueError("--read-ratio must be between 0 and 1")
    if args.keyspace <= 0:
        raise ValueError("--keyspace must be > 0")
    if args.value_size <= 0:
        raise ValueError("--value-size must be > 0")

    config = LoadConfig(
        host=args.host,
        port=args.port,
        db=args.db,
        password=args.password,
        concurrency=args.concurrency,
        operations=args.operations,
        read_ratio=args.read_ratio,
        keyspace=args.keyspace,
        value_size=args.value_size,
        ttl_seconds=args.ttl_seconds,
        warmup_operations=args.warmup_operations,
    )

    try:
        result = await run_load_profile(config)
    except RedisConnectionError as exc:
        print(
            f"Redis connection failed ({exc}). "
            "Start Redis first, then rerun this profiler."
        )
        raise SystemExit(2) from exc

    print("\nAsync Redis Load Profile")
    print("========================")
    print(f"Total operations: {result.total_operations}")
    print(f"Elapsed:          {result.elapsed_seconds:.3f} sec")
    print(f"Throughput:       {result.throughput:,.2f} ops/sec")
    print(f"Errors:           {result.errors} ({result.error_rate:.2f}%)")
    print(f"Latency p50:      {_percentile(result.latencies_ms, 50):.3f} ms")
    print(f"Latency p95:      {_percentile(result.latencies_ms, 95):.3f} ms")
    print(f"Latency p99:      {_percentile(result.latencies_ms, 99):.3f} ms")


if __name__ == "__main__":
    asyncio.run(_main())
