"""
app.py
======

Interactive Production Dashboard for Matrix-Based Visual Secret Sharing.

Built with Streamlit, this application provides a polished, responsive
interface for the Naor-Shamir (2,2) Threshold VSS engine implemented in
``core_engine.py``.

Layout Structure
----------------
1. **Source Input**      -- Original uploaded asset preview.
2. **Share Matrix 1 & 2**-- Both shares rendered side-by-side, each with
                            an independent PNG download button.
3. **Reconstruction**    -- The overlaid decrypted output.

A sidebar success banner summarizes the mathematical properties
demonstrated by the underlying scheme: Perfect Secrecy,
Computational-Free Decryption, and Contrast Constraints.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import io

import numpy as np
import streamlit as st
from PIL import Image

from core_engine import VisualSecretSharingEngine

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Matrix-Based Visual Secret Sharing",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Cached engine singleton
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def get_engine() -> VisualSecretSharingEngine:
    """Instantiate and cache a single VSS engine across reruns."""
    return VisualSecretSharingEngine()


ENGINE: VisualSecretSharingEngine = get_engine()


# ---------------------------------------------------------------------------
# Sidebar: Mathematical property summary banner
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("📐 Mathematical Properties")
    st.success(
        """
**Scheme Verification Summary**

This dashboard demonstrates the formal guarantees of the
Naor-Shamir (2,2) Threshold Visual Cryptography Scheme:

✅ **Perfect Secrecy** — Each individual share is a uniformly
random bit pattern with Shannon Entropy H = 1.0 bit/sub-pixel.
Formally, P(X = x | S₁ = s₁) = P(X = x); zero mutual information
I(X; S₁) = 0 leaks from either share alone.

✅ **Computational-Free Decryption** — Reconstruction requires no
key material and no arithmetic computation. Decryption is achieved
purely by the Human Visual System performing a physical OR
(transparency stacking) of the two shares.

✅ **Contrast Constraints** — White secret regions reconstruct at
exactly 50% grey light transmission while black regions
reconstruct at 0%, yielding the Naor-Shamir relative contrast
α = Δw/m = (4 − 2)/4 = 1/2 — i.e. an irreducible 50% geometric
transmission loss inherent to the m = 4 expansion.
"""
    )
    st.divider()
    st.caption(
        "BSc Final Year Project · Pure NumPy + Pillow implementation · "
        "No external cryptographic libraries."
    )


# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------

st.title("🔐 Matrix-Based Visual Secret Sharing")
st.markdown(
    "Upload a PNG or JPG image to split it into two cryptographically "
    "independent shares using the **Naor-Shamir (2,2) Threshold Scheme**. "
    "Overlaying both shares reconstructs the secret — no key required."
)
st.divider()

# ---------------------------------------------------------------------------
# File uploader
# ---------------------------------------------------------------------------

uploaded_file = st.file_uploader(
    "📤 Upload Source Image",
    type=["png", "jpg", "jpeg"],
    help="Accepted formats: PNG and JPG. Images are binarized at the "
    "strict midpoint threshold of 128 before GF(2) mapping.",
)

if uploaded_file is None:
    st.info("⬆️ Please upload a PNG or JPG image to begin the encryption pipeline.")
    st.stop()

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

image_bytes: bytes = uploaded_file.getvalue()

try:
    source_pil: Image.Image = Image.open(io.BytesIO(image_bytes))
except Exception:
    st.error("The uploaded file could not be decoded as a valid image.")
    st.stop()

gf2_secret: np.ndarray = ENGINE.load_and_binarize(image_bytes)
share1, share2 = ENGINE.encrypt(gf2_secret)
reconstructed: np.ndarray = ENGINE.decrypt(share1, share2)

share1_png: bytes = ENGINE.binary_to_png_bytes(share1)
share2_png: bytes = ENGINE.binary_to_png_bytes(share2)
reconstructed_png: bytes = ENGINE.reconstruct_to_png_bytes(reconstructed)

source_display: Image.Image = source_pil.convert("L")

# ---------------------------------------------------------------------------
# Section 1: Source Input
# ---------------------------------------------------------------------------

st.header("1️⃣ Source Input")
col_meta_a, col_meta_b, col_meta_c = st.columns(3)
col_meta_a.metric("Original Dimensions", f"{source_pil.width} × {source_pil.height}")
col_meta_b.metric("GF(2) Black Pixels", f"{int(gf2_secret.sum())}")
col_meta_c.metric("Expansion Factor", "m = 4 (2×2)")

st.image(
    source_display,
    caption=f"Grayscale source: `{uploaded_file.name}`",
    use_container_width=True,
)
st.divider()

# ---------------------------------------------------------------------------
# Section 2: Share Matrix 1 & 2 (side-by-side)
# ---------------------------------------------------------------------------

st.header("2️⃣ Generated Share Matrices")
st.markdown(
    "Each share is exactly **double** the height and width of the source "
    "(2M × 2N) and individually reveals **zero** information about the secret."
)

share_col_left, share_col_right = st.columns(2)

with share_col_left:
    st.subheader("🧩 Share Matrix 1")
    st.image(
        share1_png,
        caption=f"Share S₁ — dimensions {share1.shape[0]} × {share1.shape[1]}",
        use_container_width=True,
    )
    st.download_button(
        label="⬇️ Download Share 1 (PNG)",
        data=share1_png,
        file_name="vss_share_1.png",
        mime="image/png",
        use_container_width=True,
    )

with share_col_right:
    st.subheader("🧩 Share Matrix 2")
    st.image(
        share2_png,
        caption=f"Share S₂ — dimensions {share2.shape[0]} × {share2.shape[1]}",
        use_container_width=True,
    )
    st.download_button(
        label="⬇️ Download Share 2 (PNG)",
        data=share2_png,
        file_name="vss_share_2.png",
        mime="image/png",
        use_container_width=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Reconstruction
# ---------------------------------------------------------------------------

st.header("3️⃣ Reconstructed Overlaid Output")
st.markdown(
    "Reconstruction applies the vectorized maximum operation "
    "`np.maximum(S₁, S₂)`, simulating physical transparency stacking. "
    "White regions resolve to 50% grey; black regions resolve to full opacity."
)

recon_col_img, recon_col_btn = st.columns([4, 1])

with recon_col_img:
    st.image(
        reconstructed_png,
        caption=(
            f"Reconstruction R = S₁ ∨ S₂ — dimensions "
            f"{reconstructed.shape[0]} × {reconstructed.shape[1]}"
        ),
        use_container_width=True,
    )

with recon_col_btn:
    st.download_button(
        label="⬇️ Download Reconstruction (PNG)",
        data=reconstructed_png,
        file_name="vss_reconstruction.png",
        mime="image/png",
        use_container_width=True,
    )

st.caption(
    "Note: the 50% grey wash across formerly-white areas is the expected "
    "contrast loss dictated by the m = 4 pixel expansion of the "
    "Naor-Shamir basis matrices — not an implementation defect."
)