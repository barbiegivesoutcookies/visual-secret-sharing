# Appendix A: Requirement Traceability Matrix (RTM)

## A.1 Purpose

This appendix provides a structured Requirement Traceability Matrix linking
every formal project requirement (Req ID) to its design realization, source
code implementation site, automated validation point, and verification
status. The RTM guarantees bidirectional traceability: every requirement is
verifiably implemented, and every implementation artifact traces back to at
least one requirement.

## A.2 Traceability Matrix

| Req ID | Requirement Description | Priority | Design Artifact | Implementation Site | Validation Point | Status |
|---|---|---|---|---|---|---|
| REQ-01 | Map digital images into finite field GF(2) via strict threshold binarization at midpoint 128 (≥128 → 0 White, <128 → 1 Black) | Critical | Chapter 3, Def. 3.2 | `core_engine.py` → `VisualSecretSharingEngine.load_and_binarize`, `binarize_array` | Manual inspection of GF(2) output; `TestInputValidation.test_non_2d_secret_raises` | ✅ Verified |
| REQ-02 | Implement the formal Naor-Shamir 2×2 pixel expansion: white pixels (0) yield linearly dependent (identical) blocks from C₀; black pixels (1) yield linearly independent, fully inverted ordered pairs from C₁ | Critical | Chapter 3, Defs. 3.3–3.4 | `core_engine.py` → `C0_BASIS`, `C1_PAIRS`, `_select_basis_block`, `encrypt` | `TestMatrixSpatialExpansionDimensions.test_matrix_spatial_expansion_dimensions`; `TestIndividualShareSecrecy.test_white_blocks_are_linearly_dependent_black_independent` | ✅ Verified |
| REQ-03 | Ensure individual shares exhibit perfect Shannon Entropy H = 1.0 via a true uniform random bit selector (`random.randint(0, 1)`) | Critical | Chapter 3, Thm. 3.1, Cor. 3.1 | `core_engine.py` → `_select_basis_block` | `TestShannonEntropyBounds.test_shannon_entropy_bounds` (asserts H = 1.0 ± 1e-9) | ✅ Verified |
| REQ-04 | Implement reconstruction via optimized vector maximum comparison (`np.maximum`) simulating physical transparency overlaying | Critical | Chapter 3, Def. 3.5; Chapter 4, §4.3.4 | `core_engine.py` → `decrypt` | `TestReconstructionCorrectness.test_reconstruction_preserves_secret_topology` | ✅ Verified |
| REQ-05 | Enforce the contrast constraint: black regions reconstruct fully opaque (weight 4/4); white regions reconstruct at 50% grey (weight 2/4) | High | Chapter 3, Thm. 3.2, Cor. 3.2 | `core_engine.py` → `encrypt` / `decrypt` interaction | `TestReconstructionCorrectness.test_black_pixels_reconstruct_fully_opaque`; `test_white_pixels_reconstruct_at_half_transmission` | ✅ Verified |
| REQ-06 | Provide comprehensive type hinting and PEP 8 docstrings for all public methods | Medium | Coding standards §2 | `core_engine.py` (all methods annotated) | Static review; IDE type-checker pass | ✅ Verified |
| REQ-07 | Build a responsive Streamlit dashboard accepting PNG/JPG uploads | High | UI spec §3.1 | `app.py` → `st.file_uploader(type=["png","jpg","jpeg"])` | Manual UAT: upload PNG and JPG assets | ✅ Verified |
| REQ-08 | Display structured vertical layout: (1) Source Input, (2) Shares side-by-side with independent downloads, (3) Reconstructed Output | High | UI spec §3.2 | `app.py` sections 1️⃣ / 2️⃣ / 3️⃣ | Manual UAT: visual layout inspection | ✅ Verified |
| REQ-09 | Sidebar success banner summarizing Perfect Secrecy, Computational-Free Decryption, and Contrast Constraints | High | UI spec §3.3 | `app.py` sidebar `st.success` block | Manual UAT: content review against Chapter 3 claims | ✅ Verified |
| REQ-10 | Automated test asserting exact Shannon Entropy = 1.0 on a highly structured geometric image using `math.log2` and sub-pixel frequency counts | Critical | Test plan §5.1 | `test_cryptography.py` → `compute_shannon_entropy`, `TestShannonEntropyBounds` | `python -m unittest test_cryptography -v` → OK | ✅ Verified |
| REQ-11 | Automated test verifying share dimensions are exactly 2M × 2N | Critical | Test plan §5.2 | `test_cryptography.py` → `TestMatrixSpatialExpansionDimensions` | `python -m unittest test_cryptography -v` → OK (5 sub-cases incl. asymmetric/minimal/extreme) | ✅ Verified |
| REQ-12 | Use only pure NumPy and Pillow; no external cryptographic libraries | Critical | Constraint register §1.2 | `requirements.txt` (numpy, pillow, streamlit only) | Dependency audit of `requirements.txt` and import graph | ✅ Verified |
| REQ-13 | Pin stable dependency versions for reproducible environments | High | Deployment spec §6 | `requirements.txt`: numpy==1.26.4, pillow==10.3.0, streamlit==1.35.0 | Fresh `py -m venv .venv` + `pip install -r requirements.txt` on clean host | ✅ Verified |
| REQ-14 | Document virtual environment initialization (`py -m venv .venv`) and activation (`.venv\Scripts\Activate.ps1`) | High | Deployment spec §6 | `README.md` → Installation & Environment Setup | Fresh-host walkthrough | ✅ Verified |
| REQ-15 | Achieve O(M × N) time complexity across the full pipeline | High | Chapter 4, Thm. 4.1 | `core_engine.py` (single-pass stages) | Analytical proof (Ch. 4); empirical timing table §4.5 | ✅ Verified |
| REQ-16 | Bound space complexity at O(M × N) under a 9MN-byte matrix cache limit | High | Chapter 4, Def. 4.1, Thm. 4.2 | `core_engine.py` allocation profile | Liveness trace of `run_full_pipeline`; Ch. 4 Table 4.1 | ✅ Verified |
| REQ-17 | Defensive input validation raising `ValueError` on malformed inputs | Medium | Robustness spec §7 | `core_engine.py` guards in `_select_basis_block`, `encrypt`, `decrypt`, `binary_to_png_bytes` | `TestInputValidation` (4 test cases) | ✅ Verified |
| REQ-18 | Publishable academic documentation: GF(2) definitions, basis sets, Bayes' Theorem secrecy proof, contrast proof, complexity analysis, RTM | High | Dissertation outline | `docs/chapter3_mathematical_theory.md`, `docs/chapter4_performance_analysis.md`, `docs/appendix_rtm.md` | Supervisor review; cross-reference audit against code | ✅ Verified |

## A.3 Verification Legend

| Status | Meaning |
|---|---|
| ✅ Verified | Validated by automated test execution, analytical proof, or documented manual UAT with passing outcome |

## A.4 Coverage Summary

- **Total requirements:** 18
- **Critical priority:** 7 (REQ-01…05, REQ-10, REQ-12)
- **Automated validation coverage:** 11 of 18 requirements validated by executable tests in `test_cryptography.py`; remaining 7 validated by analytical proof, static review, or documented manual UAT.
- **Untraced requirements:** 0
- **Orphaned implementations:** 0

Bidirectional traceability is complete: every requirement maps to at least
one validation point, and every validation point maps back to at least one
requirement.