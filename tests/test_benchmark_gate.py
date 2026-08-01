from __future__ import annotations

import unittest
from argparse import Namespace

from benchmarks.compare_benchmarks import compare_payloads
from benchmarks.gate_benchmarks import median_payload, resolve_gate_config


class BenchmarkGateTests(unittest.TestCase):
    def test_compare_payloads_detects_throughput_and_latency_regressions(self) -> None:
        baseline = {
            "results": {
                "sqlite": {
                    "append_records_per_sec": 100.0,
                    "verify_records_per_sec": 100.0,
                    "graph_descendants_sec": 1.0,
                    "authorization_verify_sec": 1.0,
                    "query_latency_ms": 1.0,
                    "replay_sec": 1.0,
                    "memory_peak_mb": 1.0,
                    "disk_usage_bytes": 100.0,
                }
            }
        }
        current = {
            "results": {
                "sqlite": {
                    "append_records_per_sec": 80.0,  # -20% throughput regression
                    "verify_records_per_sec": 120.0,
                    "graph_descendants_sec": 1.3,  # +30% latency regression
                    "authorization_verify_sec": 1.0,
                    "query_latency_ms": 1.0,
                    "replay_sec": 1.0,
                    "memory_peak_mb": 1.0,
                    "disk_usage_bytes": 100.0,
                }
            }
        }
        _, failures = compare_payloads(
            baseline,
            current,
            throughput_regression_pct=10.0,
            latency_regression_pct=15.0,
        )
        self.assertTrue(any("append_records_per_sec" in entry for entry in failures))
        self.assertTrue(any("graph_descendants_sec" in entry for entry in failures))

    def test_median_payload_uses_median_per_metric(self) -> None:
        run_payloads = [
            {
                "results": {
                    "sqlite": {
                        "append_records_per_sec": 100.0,
                        "verify_records_per_sec": 100.0,
                        "graph_descendants_sec": 10.0,
                        "authorization_verify_sec": 2.0,
                        "query_latency_ms": 3.0,
                        "replay_sec": 4.0,
                        "memory_peak_mb": 5.0,
                        "disk_usage_bytes": 6.0,
                    }
                }
            },
            {
                "results": {
                    "sqlite": {
                        "append_records_per_sec": 200.0,
                        "verify_records_per_sec": 200.0,
                        "graph_descendants_sec": 20.0,
                        "authorization_verify_sec": 3.0,
                        "query_latency_ms": 4.0,
                        "replay_sec": 5.0,
                        "memory_peak_mb": 6.0,
                        "disk_usage_bytes": 7.0,
                    }
                }
            },
            {
                "results": {
                    "sqlite": {
                        "append_records_per_sec": 1000.0,
                        "verify_records_per_sec": 1000.0,
                        "graph_descendants_sec": 200.0,
                        "authorization_verify_sec": 20.0,
                        "query_latency_ms": 30.0,
                        "replay_sec": 40.0,
                        "memory_peak_mb": 50.0,
                        "disk_usage_bytes": 60.0,
                    }
                }
            },
        ]
        payload = median_payload(run_payloads, records=200)
        sqlite = payload["results"]["sqlite"]
        self.assertEqual(sqlite["append_records_per_sec"], 200.0)
        self.assertEqual(sqlite["graph_descendants_sec"], 20.0)
        self.assertEqual(payload["runs"], 3)

    def test_compare_payloads_applies_threshold_overrides(self) -> None:
        baseline = {
            "results": {
                "in_memory": {
                    "append_records_per_sec": 100.0,
                    "verify_records_per_sec": 100.0,
                    "graph_descendants_sec": 1.0,
                    "authorization_verify_sec": 1.0,
                    "query_latency_ms": 1.0,
                    "replay_sec": 1.0,
                    "memory_peak_mb": 1.0,
                    "disk_usage_bytes": 1.0,
                }
            }
        }
        current = {
            "results": {
                "in_memory": {
                    "append_records_per_sec": 85.0,  # -15%
                    "verify_records_per_sec": 100.0,
                    "graph_descendants_sec": 1.0,
                    "authorization_verify_sec": 1.0,
                    "query_latency_ms": 1.20,  # +20%
                    "replay_sec": 1.0,
                    "memory_peak_mb": 1.0,
                    "disk_usage_bytes": 1.0,
                }
            }
        }
        _, failures = compare_payloads(
            baseline,
            current,
            throughput_regression_pct=10.0,
            latency_regression_pct=15.0,
            threshold_overrides={
                "in_memory": {
                    "append_records_per_sec": 20.0,
                    "query_latency_ms": 25.0,
                }
            },
        )
        self.assertEqual(failures, [])

    def test_resolve_gate_config_uses_mode_and_allows_overrides(self) -> None:
        quick = resolve_gate_config(
            Namespace(
                mode="quick",
                records=None,
                runs=None,
                throughput_regression_pct=None,
                latency_regression_pct=None,
            )
        )
        self.assertEqual(quick["records"], 80)
        self.assertEqual(quick["runs"], 1)

        pr = resolve_gate_config(
            Namespace(
                mode="pr",
                records=None,
                runs=None,
                throughput_regression_pct=None,
                latency_regression_pct=None,
            )
        )
        nightly = resolve_gate_config(
            Namespace(
                mode="nightly",
                records=None,
                runs=None,
                throughput_regression_pct=None,
                latency_regression_pct=None,
            )
        )
        self.assertEqual(pr["records"], 120)
        self.assertEqual(pr["runs"], 2)
        self.assertEqual(nightly["records"], 200)
        self.assertEqual(nightly["runs"], 3)

        overridden = resolve_gate_config(
            Namespace(
                mode="quick",
                records=140,
                runs=2,
                throughput_regression_pct=11.0,
                latency_regression_pct=22.0,
            )
        )
        self.assertEqual(overridden["records"], 140)
        self.assertEqual(overridden["runs"], 2)
        self.assertEqual(overridden["throughput_regression_pct"], 11.0)
        self.assertEqual(overridden["latency_regression_pct"], 22.0)


if __name__ == "__main__":
    unittest.main()
