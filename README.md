# 🔐 Matrix-Based Visual Secret Sharing (VSS)

**BSc Final Year Project — Naor-Shamir (2,2) Threshold Visual Cryptography Scheme**

A production-ready, academically rigorous implementation of Visual Secret
Sharing that splits any digital image into two cryptographically independent
shares. Neither share alone reveals **any** information about the secret;
overlaying both shares physically reconstructs the image with **zero
computational cost** — decryption is performed entirely by the Human Visual
System.

---

## 📖 Table of Contents

- [🔐 Matrix-Based Visual Secret Sharing (VSS)](#-matrix-based-visual-secret-sharing-vss)
  - [📖 Table of Contents](#-table-of-contents)
  - [🌟 Project Overview](#-project-overview)
  - [🧮 Mathematical Foundation](#-mathematical-foundation)
    - [Basis Matrices](#basis-matrices)
  - [✅ Prerequisites](#-prerequisites)
  - [🛠 Installation \& Environment Setup](#-installation--environment-setup)
    - [Step 1 — Clone / open the project directory](#step-1--clone--open-the-project-directory)
    - [Step 2 — Initialize the virtual environment](#step-2--initialize-the-virtual-environment)
    - [Step 3 — Activate the virtual environment](#step-3--activate-the-virtual-environment)
    - [Step 4 — Install pinned dependencies](#step-4--install-pinned-dependencies)
  - [▶️ Running the Dashboard](#️-running-the-dashboard)
  - [🧪 Running the Security Test Suite](#-running-the-security-test-suite)
  - [🏗 Project Architecture](#-project-architecture)
    - [Core Engine Data Flow](#core-engine-data-flow)
  - [📚 Academic Documentation](#-academic-documentation)
  - [📋 Requirement Traceability Matrix (Summary)](#-requirement-traceability-matrix-summary)
  - [📄 License](#-license)

---

## 🌟 Project Overview

| Property | Guarantee |
|---|---|
| **Perfect Secrecy** | `P(X = x \| S₁ = s₁) = P(X = x)` — Shannon Entropy of each share is exactly H = 1.0 |
| **Decryption Model** | Computational-free; physical transparency stacking (logical OR) |
| **Pixel Expansion** | m = 4 (each share is exactly 2M × 2N) |
| **Contrast Constraint** | White → 50% grey; Black → 100% opaque (α = Δw/m = 2/4 = 1/2) |
| **Cryptographic Libraries** | **None** — pure NumPy + Pillow; security is information-theoretic |

---

## 🧮 Mathematical Foundation

All pixel data is mapped into the finite field **GF(2)** via strict threshold
binarization at the midpoint value 128:

```text
b(x, y) = 0   if gray(x, y) ≥ 128   (White / Transparent)
b(x, y) = 1   if gray(x, y) <  128   (Black / Opaque)
```

### Basis Matrices

**C₀ — White (0) secret pixels** (linearly dependent rows):

```text
C₀ ∈ { ┌ 1 0 ┐   ┌ 0 1 ┐   ┌ 1 0 ┐   ┌ 0 1 ┐ }
       └ 1 0 ┘ , └ 0 1 ┘ , └ 0 1 ┘ , └ 1 0 ┘
```

**C₁ — Black (1) secret pixels** (four ordered complementary pairs):

```text
C₁ ∈ { ( B₁ , B₂ ) , ( B₂ , B₁ ) , ( B₃ , B₄ ) , ( B₄ , B₃ ) }
```

For a **white** secret pixel, the SAME C₀ block is assigned to both shares;
overlaying the two share blocks reproduces exactly **2 of 4** black
sub-pixels (50% grey). For a **black** secret pixel, one ordered
complementary C₁ pair is split across the two shares; overlaying them
reproduces **4 of 4** black sub-pixels (fully opaque). Because all four
ordered pairs are equally likely, Share 1's block distribution is uniform
over {B₁..B₄} given *either* secret value — the exact condition for
block-level perfect secrecy. Full derivations, the Bayes' Theorem secrecy
proof, and the contrast analysis are provided in
[`docs/chapter3_mathematical_theory.md`](docs/chapter3_mathematical_theory.md).

---

## ✅ Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Operating System | Windows 10 / 11 | PowerShell activation scripts included |
| Python | 3.10+ | Verified against 3.11 and 3.12 |
| pip | 23.0+ | Bundled with Python |
| Disk Space | ~250 MB | Virtual environment + dependencies |
| RAM | 4 GB | Comfortable headroom for large images |

Verify your installation:

```powershell
py --version
py -m pip --version
```

---

## 🛠 Installation & Environment Setup

### Step 1 — Clone / open the project directory

```powershell
cd C:\Users\hp\Desktop\vss_project
```

### Step 2 — Initialize the virtual environment

```powershell
py -m venv .venv
```

### Step 3 — Activate the virtual environment

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Command Prompt (alternative):

```cmd
.venv\Scripts\activate.bat
```

> ⚠️ If PowerShell blocks script execution, relax the policy for the current
> session only:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### Step 4 — Install pinned dependencies

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

`requirements.txt` pins stable, mutually compatible versions:

```text
numpy==1.26.4
pillow==10.3.0
streamlit==1.35.0
```

---

## ▶️ Running the Dashboard

With the virtual environment activated:

```powershell
streamlit run app.py
```

Streamlit will launch the interactive production dashboard at
`http://localhost:8501`. The interface presents:

1. **Source Input** — the uploaded PNG/JPG preview with live GF(2) statistics.
2. **Share Matrix 1 & 2** — rendered side-by-side, each independently
   downloadable as a PNG artifact.
3. **Reconstructed Overlaid Output** — the stacked decryption result.

The sidebar displays a persistent summary of the mathematical properties
demonstrated: **Perfect Secrecy**, **Computational-Free Decryption**, and
**Contrast Constraints**.

---

## 🧪 Running the Security Test Suite

With the virtual environment activated:

```powershell
python -m unittest test_cryptography -v
```

Expected output terminates with:

```text
OK
```

The suite validates:

- **`test_shannon_entropy_bounds`** — encrypts a highly structured geometric
  image, flattens both shares, computes exact Shannon Entropy via
  `math.log2` over sub-pixel frequency counts, and asserts H = 1.0 within a
  1e-9 tolerance (zero data leakage).
- **`test_matrix_spatial_expansion_dimensions`** — asserts every share is
  exactly 2M × 2N across square, asymmetric, minimal, and extreme-aspect
  inputs.
- Reconstruction correctness, contrast semantics, individual-share secrecy,
  basis-matrix rank properties, and input-validation guards.

---

## 🏗 Project Architecture

```text
vss_project/
├── core_engine.py                     # Core Naor-Shamir encryption engine
├── app.py                             # Streamlit production dashboard
├── test_cryptography.py               # Automated unittest security suite
├── requirements.txt                   # Pinned dependency manifest
├── README.md                          # This document
└── docs/
    ├── chapter3_mathematical_theory.md   # Formal proofs & field definitions
    ├── chapter4_performance_analysis.md  # Big-O complexity analysis
    └── appendix_rtm.md                   # Requirement Traceability Matrix
```

### Core Engine Data Flow

```text
Raw Bytes ──► PIL Decode ──► Grayscale ──► Threshold(128) ──► GF(2) Matrix (M×N)
                                                                    │
                                              ┌─────────────────────┘
                                              ▼
                              Uniform Random Selector (randint 0..1)
                                              │
                                   ┌──────────┴──────────┐
                                   ▼                     ▼
                             C₀ / C₁ lookup         Block placement
                                   │                     │
                                   ▼                     ▼
                            Share S₁ (2M×2N) ◄───── Share S₂ (2M×2N)
                                   │                     │
                                   └──────────┬──────────┘
                                              ▼
                                    np.maximum(S₁, S₂)   ← OR-overlay
                                              │
                                              ▼
                                  Reconstructed Secret (2M×2N)
```

---

## 📚 Academic Documentation

Complete dissertation chapters are included in the `docs/` directory:

| Document | Contents |
|---|---|
| [`docs/chapter3_mathematical_theory.md`](docs/chapter3_mathematical_theory.md) | GF(2) field definitions, exact basis matrix sets, step-by-step Bayes' Theorem secrecy proof, rigorous 50% contrast evaluation |
| [`docs/chapter4_performance_analysis.md`](docs/chapter4_performance_analysis.md) | Time complexity O(M·N), space complexity O(M·N) under a 9MN-byte cache limit, empirical scaling discussion |
| [`docs/appendix_rtm.md`](docs/appendix_rtm.md) | Structured Requirement Traceability Matrix linking Req IDs to system validation points |

---

## 📋 Requirement Traceability Matrix (Summary)

Full matrix in [`docs/appendix_rtm.md`](docs/appendix_rtm.md).

| Req ID | Requirement | Validation Point |
|---|---|---|
| REQ-01 | GF(2) mapping via threshold 128 | `core_engine.load_and_binarize` |
| REQ-02 | Naor-Shamir 2×2 expansion | `core_engine.encrypt`; `test_matrix_spatial_expansion_dimensions` |
| REQ-03 | Perfect secrecy H = 1.0 | `test_shannon_entropy_bounds` |
| REQ-04 | Computational-free decryption | `core_engine.decrypt` (`np.maximum`) |
| REQ-05 | Contrast constraint α = 1/2 (50% transmission loss) | `test_white_pixels_reconstruct_at_half_transmission` |
| REQ-06 | Interactive dashboard | `app.py` Streamlit layout |
| REQ-07 | Reproducible environment | `requirements.txt`, README setup steps |

---

## 📄 License

Released under the MIT License for academic and educational use.

© BSc Final Year Project — Matrix-Based Visual Secret Sharing.