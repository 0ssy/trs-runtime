from __future__ import annotations

import unittest

from runtime.benchmark import run_benchmarks


class BenchmarkSmokeTests(unittest.TestCase):
    def test_run_benchmarks_returns_expected_backends_and_metrics(self) -> None:
        results = run_benchmarks(records=120)
        for backend in ("in_memory", "sqlite", "lmdb", "rocksdb"):
            self.assertIn(backend, results)
            metrics = results[backend]
            self.assertGreater(metrics["append_records_per_sec"], 0.0)
            self.assertGreater(metrics["verify_records_per_sec"], 0.0)
            self.assertGreaterEqual(metrics["query_latency_ms"], 0.0)
            self.assertGreaterEqual(metrics["disk_usage_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
