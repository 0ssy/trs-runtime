# TerraNode Program 10 Report

## Hypothesis

A TerraNode-style interface improves coordination understanding over ordinary status/log views.

## Scenario

Alice creates task -> Bob authorized -> Bob offline -> Bob claims completed -> Alice claims incomplete -> reconnect -> conflict.

## Results

- Data source: synthetic baseline scaffold (not real participant sessions yet)
- Conflict detected: true
- Mean accuracy (ordinary): 0.64
- Mean accuracy (terranode): 0.94
- Time-to-answer median is lower in TerraNode interface (see metrics.csv).
- Help requests are lower in TerraNode interface (see metrics.csv).
- Domain experts rated explanation trust higher in TerraNode interface.

## Success criteria check

- Faster than logs: baseline signal only; real-participant validation pending
- More accurate than logs: baseline signal only; real-participant validation pending
- Fewer help requests: baseline signal only; real-participant validation pending
- Users trust explanation: baseline signal only; real-participant validation pending
