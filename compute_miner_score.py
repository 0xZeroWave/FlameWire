import argparse
import time
from typing import List, Optional

import requests

from flamewire.validator.scoring import MinerScorer


def _rpc_call(
    session: requests.Session, url: str, method: str, params: Optional[List[str]] = None
) -> bool:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    resp = session.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json().get("result") is not None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute miner score by querying a Bittensor archive node directly"
    )
    parser.add_argument("--rpc-url", required=True, help="Archive node RPC endpoint")
    parser.add_argument(
        "--checks", type=int, default=25, help="Number of RPC calls to sample"
    )
    args = parser.parse_args()

    last_checks: List[bool] = []
    last_times: List[float] = []
    session = requests.Session()

    for _ in range(args.checks):
        start = time.perf_counter()
        try:
            success = _rpc_call(session, args.rpc_url, "chain_getBlockHash")
        except Exception:
            success = False
        elapsed_ms = (time.perf_counter() - start) * 1000
        last_checks.append(success)
        last_times.append(elapsed_ms)

    scorer = MinerScorer(window_size=args.checks)
    score, success_rate, avg_time, speed_score = scorer.score_with_metrics(
        last_checks, last_times
    )

    print(f"Score: {score:.4f}")
    print(f"  Success Rate: {success_rate:.2f}")
    print(f"  Avg Response Time: {avg_time:.2f}s")
    print(f"  Speed Score: {speed_score:.2f}")


if __name__ == "__main__":
    main()
