"""
core_engine.py
==============

Core cryptographic engine for Matrix-Based Visual Secret Sharing (VSS).

This module implements the formal Naor-Shamir (2,2) Threshold Visual
Cryptography Scheme using pure NumPy and Pillow. No external
cryptographic libraries are used; all security derives from the
information-theoretic construction of the basis matrices C_0 and C_1.

Mathematical Foundation
-----------------------
All pixel operations are mapped into the finite field GF(2), where:

    GF(2) = ({0, 1}, +, x)

with addition defined as XOR and multiplication as logical AND.
A source image is binarized with a strict threshold at the midpoint
value 128: pixels >= 128 map to 0 (White / Transparent) and pixels
< 128 map to 1 (Black / Opaque).

Each binary secret pixel is expanded into a 2x2 block per share,
yielding a total pixel expansion factor m = 4 (each share is exactly
double the width and height of the original image).

Basis Matrices (Naor-Shamir, 1994)
----------------------------------
Denote the four admissible weight-2 blocks:

    B1 = [1 0]   B2 = [0 1]   B3 = [1 0]   B4 = [0 1]
         [1 0]        [0 1]        [0 1]        [1 0]

For a white (0) secret pixel, ONE block is drawn uniformly from C_0 and
the IDENTICAL block is assigned to both shares:

    C_0 = { B1, B2, B3, B4 }

Because both shares carry the same block, whose columns each hold
exactly one black sub-pixel, the physical overlay reproduces exactly
2 of 4 black sub-pixels -> the reconstructed pixel appears 50% grey.

For a black (1) secret pixel, ONE ordered complementary pair is drawn
uniformly from C_1 and split across the two shares:

    C_1 = { (B1, B2), (B2, B1), (B3, B4), (B4, B3) }

Each pair consists of completely inverted (complementary) blocks, so
the overlay reproduces 4 of 4 black sub-pixels -> fully opaque.

Perfect Secrecy
---------------
Under both constructions, Share 1's block is distributed UNIFORMLY over
{B1, B2, B3, B4} independent of the secret bit, hence:

    P(X = x | S1 = s1) = P(X = x)   for all x in {0, 1}

which yields Shannon entropy H(S1) = H(S2) = 1.0 bits per sub-pixel
and zero mutual information I(X; S1) = 0.

Reconstruction
--------------
Reconstruction simulates physical transparency stacking via the
logical OR of the two shares, computed in vectorized form with
``np.maximum`` for optimal performance.

Author: BSc Final Year Project - Matrix-Based Visual Secret Sharing
License: MIT
"""

from __future__ import annotations

import io
import random
from typing import Final, Tuple

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: Strict binarization midpoint threshold (inclusive upper bound for white).
BINARIZATION_THRESHOLD: Final[int] = 128

#: Pixel expansion factor m of the Naor-Shamir (2,2) scheme (m = n! style 2x2).
PIXEL_EXPANSION: Final[int] = 2

#: Basis matrix C_0 for white (0) secret pixels, shape (4, 2, 2).
#: Every candidate block places exactly ONE black sub-pixel per column
#: pair, i.e. its two rows are linearly dependent over GF(2). When the
#: SAME block is assigned to both shares, the physical overlay (OR)
#: reproduces exactly 2 of 4 black sub-pixels -> 50% grey (white).
C0_BASIS: Final[np.ndarray] = np.array(
    [
        [[1, 0], [1, 0]],  # vertical stripe variant A
        [[0, 1], [0, 1]],  # vertical stripe variant B
        [[1, 0], [0, 1]],  # diagonal variant A
        [[0, 1], [1, 0]],  # diagonal variant B
    ],
    dtype=np.uint8,
)

#: Basis collection C_1 for black (1) secret pixels, stored as ORDERED
#: complementary PAIRS, shape (4, 2, 2, 2). The four ordered pairs
#: (B1,B2), (B2,B1), (B3,B4), (B4,B3) guarantee that Share 1's block is
#: distributed uniformly over {B1, B2, B3, B4} GIVEN EITHER secret bit,
#: which is precisely the condition for block-level perfect secrecy.
#: Each pair consists of completely inverted blocks whose overlay
#: reproduces 4 of 4 black sub-pixels -> fully opaque (black).
C1_PAIRS: Final[np.ndarray] = np.array(
    [
        [[[1, 0], [1, 0]], [[0, 1], [0, 1]]],  # ordered pair (B1, B2)
        [[[0, 1], [0, 1]], [[1, 0], [1, 0]]],  # ordered pair (B2, B1)
        [[[1, 0], [0, 1]], [[0, 1], [1, 0]]],  # ordered pair (B3, B4)
        [[[0, 1], [1, 0]], [[1, 0], [0, 1]]],  # ordered pair (B4, B3)
    ],
    dtype=np.uint8,
)


class VisualSecretSharingEngine:
    """
    Implements the Naor-Shamir (2,2) Threshold Visual Secret Sharing scheme.

    The engine exposes three primary operations:

    1. :meth:`binarize_image`   -- Map an RGB/grayscale image into GF(2).
    2. :meth:`encrypt`          -- Split a binary secret into two shares.
    3. :meth:`decrypt`          -- Reconstruct the secret by OR-stacking.

    Attributes:
        threshold: Binarization midpoint used during GF(2) mapping.
    """

    def __init__(self, threshold: int = BINARIZATION_THRESHOLD) -> None:
        """
        Initialize the VSS engine.

        Args:
            threshold: Grayscale midpoint used for strict threshold
                binarization. Defaults to 128 per the specification.
        """
        self.threshold: int = threshold

    # ------------------------------------------------------------------
    # Stage 1: Finite Field GF(2) Mapping
    # ------------------------------------------------------------------

    def load_and_binarize(self, image_bytes: bytes) -> np.ndarray:
        """
        Load raw image bytes and map them into the finite field GF(2).

        The image is converted to grayscale ('L' mode), then every pixel
        is binarized with a strict threshold at ``self.threshold``:

            b(x, y) = 0  if gray(x, y) >= threshold   (White / Transparent)
            b(x, y) = 1  if gray(x, y) <  threshold   (Black / Opaque)

        Args:
            image_bytes: Raw encoded image bytes (PNG or JPG).

        Returns:
            A 2-D ``numpy.ndarray`` of dtype ``uint8`` containing only
            the values 0 and 1, shape (M, N).

        Raises:
            ValueError: If ``image_bytes`` cannot be decoded as an image.
        """
        try:
            pil_image: Image.Image = Image.open(io.BytesIO(image_bytes))
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ValueError("Input bytes could not be decoded as an image.") from exc

        grayscale: Image.Image = pil_image.convert("L")
        pixel_array: np.ndarray = np.asarray(grayscale, dtype=np.uint8)

        # Strict threshold binarization into GF(2): {0, 1}.
        gf2_matrix: np.ndarray = np.where(
            pixel_array >= self.threshold, 0, 1
        ).astype(np.uint8)
        return gf2_matrix

    def binarize_array(self, pixel_array: np.ndarray) -> np.ndarray:
        """
        Binarize an already-decoded numpy pixel array into GF(2).

        Args:
            pixel_array: Array of grayscale intensities, shape (M, N),
                values in [0, 255].

        Returns:
            Binary GF(2) array of identical shape with values in {0, 1}.

        Raises:
            ValueError: If the input array is not 2-dimensional.
        """
        if pixel_array.ndim != 2:
            raise ValueError(
                f"Expected a 2-D grayscale array, received ndim={pixel_array.ndim}."
            )
        return np.where(pixel_array >= self.threshold, 0, 1).astype(np.uint8)

    # ------------------------------------------------------------------
    # Stage 2: Naor-Shamir Encryption (Share Generation)
    # ------------------------------------------------------------------

    def _select_basis_block(self, secret_bit: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Select the two 2x2 share blocks for a single secret bit.

        A true uniform random selector (``random.randint(0, 1)``) chooses
        the base configuration index, guaranteeing that each individual
        share exhibits perfect Shannon entropy H = 1.0 bit/sub-pixel.

        Args:
            secret_bit: The GF(2) secret pixel value (0 = white, 1 = black).

        Returns:
            A tuple ``(block_share1, block_share2)``, each a 2x2 uint8
            array drawn from C_0 (white) or C_1 (black).

        Raises:
            ValueError: If ``secret_bit`` is not in {0, 1}.
        """
        if secret_bit not in (0, 1):
            raise ValueError(f"Secret bit must be 0 or 1, got {secret_bit!r}.")

        # Two independent true uniform random bit selectors composed into
        # a uniform index over {0, 1, 2, 3}. Using random.randint(0, 1)
        # as the base primitive keeps the entropy source a genuine coin
        # flip while covering the full 4-element configuration space.
        first_bit: int = random.randint(0, 1)
        second_bit: int = random.randint(0, 1)
        uniform_index: int = 2 * first_bit + second_bit

        if secret_bit == 0:
            # White pixel: draw ONE block uniformly from C_0 and assign
            # the IDENTICAL block to both shares. The overlay therefore
            # reproduces exactly one black sub-pixel per column pair
            # -> 50% grey.
            block: np.ndarray = C0_BASIS[uniform_index]
            return block.copy(), block.copy()

        # Black pixel: draw ONE ordered complementary pair uniformly from
        # C_1. Because all four ordered pairs are equally likely, Share 1
        # receives each of B1..B4 with probability exactly 1/4 -- the SAME
        # marginal distribution as the white case -- while the completely
        # inverted pairing saturates the overlay at 4 of 4 black
        # sub-pixels -> fully opaque.
        pair: np.ndarray = C1_PAIRS[uniform_index]
        return pair[0].copy(), pair[1].copy()

    def encrypt(self, gf2_secret: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Encrypt a GF(2) secret image into two visually hidden shares.

        Every secret pixel is expanded into a 2x2 block on each share,
        producing output shares of shape (2M, 2N) per the m=4 expansion
        constraint of the Naor-Shamir scheme.

        Args:
            gf2_secret: Binary secret matrix of shape (M, N), values in {0, 1}.

        Returns:
            A tuple ``(share1, share2)`` of binary matrices, each of
            shape (2M, 2N), values in {0, 1}.

        Raises:
            ValueError: If the secret matrix is not 2-dimensional.
        """
        if gf2_secret.ndim != 2:
            raise ValueError(
                f"Secret must be a 2-D matrix, received ndim={gf2_secret.ndim}."
            )

        rows: int
        cols: int
        rows, cols = gf2_secret.shape

        # Pre-allocate the expanded share canvases (2M x 2N).
        share1: np.ndarray = np.zeros(
            (rows * PIXEL_EXPANSION, cols * PIXEL_EXPANSION), dtype=np.uint8
        )
        share2: np.ndarray = np.zeros_like(share1)

        # Vectorized row/col index grids for block placement.
        out_rows = np.arange(rows) * PIXEL_EXPANSION
        out_cols = np.arange(cols) * PIXEL_EXPANSION

        for i in range(rows):
            for j in range(cols):
                block1, block2 = self._select_basis_block(int(gf2_secret[i, j]))
                r: int = out_rows[i]
                c: int = out_cols[j]
                share1[r : r + PIXEL_EXPANSION, c : c + PIXEL_EXPANSION] = block1
                share2[r : r + PIXEL_EXPANSION, c : c + PIXEL_EXPANSION] = block2

        return share1, share2

    # ------------------------------------------------------------------
    # Stage 3: Reconstruction (Physical Overlay Simulation)
    # ------------------------------------------------------------------

    def decrypt(self, share1: np.ndarray, share2: np.ndarray) -> np.ndarray:
        """
        Reconstruct the secret by simulating physical overlay stacking.

        Transparency stacking corresponds to a logical OR across the
        aligned sub-pixels. This is computed with the optimized vector
        maximum comparison ``np.maximum(share1, share2)`` which is
        mathematically equivalent to element-wise OR on binary arrays
        while avoiding Python-level branching overhead.

        Args:
            share1: First binary share matrix, shape (2M, 2N).
            share2: Second binary share matrix, shape (2M, 2N).

        Returns:
            The reconstructed binary matrix of shape (2M, 2N). White
            secret regions appear as 50% grey checkerboards; black
            secret regions appear fully opaque.

        Raises:
            ValueError: If the share shapes do not match.
        """
        if share1.shape != share2.shape:
            raise ValueError(
                f"Share shapes must match: {share1.shape} vs {share2.shape}."
            )

        # Optimized vector maximum == logical OR for binary arrays.
        reconstructed: np.ndarray = np.maximum(share1, share2).astype(np.uint8)
        return reconstructed

    # ------------------------------------------------------------------
    # Utility: Binary <-> Renderable Image Conversion
    # ------------------------------------------------------------------

    @staticmethod
    def binary_to_png_bytes(binary_matrix: np.ndarray, scale: int = 8) -> bytes:
        """
        Render a binary GF(2) matrix as PNG-encoded image bytes.

        Args:
            binary_matrix: Binary array of shape (H, W), values in {0, 1}.
            scale: Integer upscaling factor applied to each sub-pixel so
                that expanded blocks remain human-inspectable. Defaults
                to 8 (nearest-neighbour magnification).

        Returns:
            PNG-encoded byte stream suitable for download or display.

        Raises:
            ValueError: If the matrix contains non-binary values.
        """
        unique_values: np.ndarray = np.unique(binary_matrix)
        if not np.all(np.isin(unique_values, (0, 1))):
            raise ValueError("Binary matrix must contain only values 0 and 1.")

        # Map GF(2) -> 8-bit luminance: 0 -> 255 (white), 1 -> 0 (black).
        luminance: np.ndarray = np.where(binary_matrix == 0, 255, 0).astype(np.uint8)
        pil_image: Image.Image = Image.fromarray(luminance, mode="L")

        if scale > 1:
            new_size: Tuple[int, int] = (
                pil_image.width * scale,
                pil_image.height * scale,
            )
            pil_image = pil_image.resize(new_size, Image.NEAREST)

        buffer: io.BytesIO = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def reconstruct_to_png_bytes(reconstructed: np.ndarray, scale: int = 8) -> bytes:
        """
        Render a reconstructed overlay matrix as PNG-encoded bytes.

        Identical rendering semantics to :meth:`binary_to_png_bytes`;
        provided as a semantically distinct entry point for the
        reconstruction pipeline stage.

        Args:
            reconstructed: Reconstructed binary array of shape (2M, 2N).
            scale: Nearest-neighbour magnification factor. Defaults to 8.

        Returns:
            PNG-encoded byte stream of the overlaid reconstruction.
        """
        return VisualSecretSharingEngine.binary_to_png_bytes(reconstructed, scale=scale)

    # ------------------------------------------------------------------
    # High-Level Convenience Pipeline
    # ------------------------------------------------------------------

    def run_full_pipeline(
        self, image_bytes: bytes
    ) -> Tuple[bytes, bytes, bytes, Tuple[int, int]]:
        """
        Execute the complete encrypt -> decrypt lifecycle on raw bytes.

        Args:
            image_bytes: Raw PNG/JPG encoded source image.

        Returns:
            A tuple ``(share1_png, share2_png, reconstructed_png, shape)``
            where each PNG entry is downloadable byte data and ``shape``
            is the (height, width) of the ORIGINAL unexpanded input.
        """
        gf2_secret: np.ndarray = self.load_and_binarize(image_bytes)
        original_shape: Tuple[int, int] = gf2_secret.shape

        share1, share2 = self.encrypt(gf2_secret)
        reconstructed: np.ndarray = self.decrypt(share1, share2)

        share1_png: bytes = self.binary_to_png_bytes(share1)
        share2_png: bytes = self.binary_to_png_bytes(share2)
        reconstructed_png: bytes = self.reconstruct_to_png_bytes(reconstructed)

        return share1_png, share2_png, reconstructed_png, original_shape


# ---------------------------------------------------------------------------
# Standalone smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Minimal deterministic demonstration on a tiny synthetic pattern.
    demo_pattern: np.ndarray = np.array(
        [
            [255, 255, 0, 0],
            [255, 255, 0, 0],
            [0, 0, 255, 255],
            [0, 0, 255, 255],
        ],
        dtype=np.uint8,
    )

    engine: VisualSecretSharingEngine = VisualSecretSharingEngine()
    demo_binary: np.ndarray = engine.binarize_array(demo_pattern)
    s1, s2 = engine.encrypt(demo_binary)
    rec: np.ndarray = engine.decrypt(s1, s2)

    print("Secret (GF(2)):")
    print(demo_binary)
    print("")
    print("Share 1 (2M x 2N):")
    print(s1)
    print("")
    print("Share 2 (2M x 2N):")
    print(s2)
    print("")
    print("Reconstructed overlay:")
    print(rec)
