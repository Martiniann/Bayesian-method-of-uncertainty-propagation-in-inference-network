# Bayesian Uncertainty Propagation — Report

> Generated on **2026-07-10 08:48 UTC**

This report summarises the Bayesian inference calculations performed on all
available datasets using the **Subjective Bayes / CTR / GLOB** pipeline.

---

## Summary

| Dataset | Prior P(H) | # Evidences | GLOB | **Posterior P(H)** |
|---------|-----------|-------------|------|-------------------|
| `data1.txt` | 0.7 | 3 | 0.52 | **0.3421** |
| `data2.txt` | 0.7 | 2 | 1.741 | **0.6352** |
| `data3.txt` | 0.7 | 7 | 0.2161 | **0.1777** |

---

## Dataset 1: `data1.txt`

| Parameter | Value |
|-----------|-------|
| Prior probability P(H) | **0.7** |
| Evidence interval | [-5.0, 5.0] |
| Number of evidences | 3 |
| Combined GLOB | 0.52 |
| **Final posterior P(H\|E₁…Eₙ)** | **0.3421** |

### Evidence breakdown

| # | P(E) | P(H\|E) | P(H\|¬E) | Guess | P(E') | P(H\|E') | Odds | λ (LS) |
|---|------|---------|----------|-------|-------|----------|------|--------|
| 1 | 0.3 | 0.86 | 0.34 | -3.0 | 0.12 | 0.484 | 0.938 | 0.402 |
| 2 | 0.1 | 0.9 | 0.1 | 0.0 | 0.1 | 0.7 | 2.3333 | 1.0 |
| 3 | 0.5 | 0.53 | 0.18 | 4.0 | 0.9 | 0.564 | 1.2936 | 0.5544 |

---

## Dataset 2: `data2.txt`

| Parameter | Value |
|-----------|-------|
| Prior probability P(H) | **0.7** |
| Evidence interval | [-5.0, 5.0] |
| Number of evidences | 2 |
| Combined GLOB | 1.741 |
| **Final posterior P(H\|E₁…Eₙ)** | **0.6352** |

### Evidence breakdown

| # | P(E) | P(H\|E) | P(H\|¬E) | Guess | P(E') | P(H\|E') | Odds | λ (LS) |
|---|------|---------|----------|-------|-------|----------|------|--------|
| 1 | 0.3 | 0.8 | 0.22 | 2.0 | 0.58 | 0.74 | 2.8462 | 1.2198 |
| 2 | 0.4 | 0.56 | 0.3 | 4.0 | 0.88 | 0.588 | 1.4272 | 0.6117 |

---

## Dataset 3: `data3.txt`

| Parameter | Value |
|-----------|-------|
| Prior probability P(H) | **0.7** |
| Evidence interval | [-5.0, 5.0] |
| Number of evidences | 7 |
| Combined GLOB | 0.2161 |
| **Final posterior P(H\|E₁…Eₙ)** | **0.1777** |

### Evidence breakdown

| # | P(E) | P(H\|E) | P(H\|¬E) | Guess | P(E') | P(H\|E') | Odds | λ (LS) |
|---|------|---------|----------|-------|-------|----------|------|--------|
| 1 | 0.5 | 0.53 | 0.18 | 4.0 | 0.9 | 0.564 | 1.2936 | 0.5544 |
| 2 | 0.6 | 0.4 | 0.3 | 2.0 | 0.76 | 0.58 | 1.381 | 0.5919 |
| 3 | 0.1 | 0.72 | 0.17 | 4.0 | 0.82 | 0.716 | 2.5211 | 1.0805 |
| 4 | 0.76 | 0.29 | 0.32 | 1.0 | 0.808 | 0.618 | 1.6178 | 0.6934 |
| 5 | 0.45 | 0.62 | 0.33 | 4.0 | 0.89 | 0.636 | 1.7473 | 0.7489 |
| 6 | 0.2 | 0.3 | 0.13 | 2.0 | 0.52 | 0.54 | 1.1739 | 0.5031 |
| 7 | 0.65 | 0.7 | 0.37 | 4.0 | 0.93 | 0.7 | 2.3333 | 1.0 |

---
