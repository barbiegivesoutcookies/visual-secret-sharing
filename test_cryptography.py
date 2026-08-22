"""
test_cryptography.py
====================

Automated security and correctness test suite for the Matrix-Based
Visual Secret Sharing engine, built on Python's native ``unittest``
framework.

Test Coverage
-------------
1. ``test_shannon_entropy_bounds``
   Feeds a highly structured geometric image through the encryption
   pipeline, flattens the resulting share arrays, computes the exact
   Shannon Entropy via ``math.log2`` over sub-pixel frequency counts,
   and asserts H = 1.0 within a tight tolerance (zero data leakage).

2. ``test_matrix_spatial_expansion_dimensions``
   Verifies that each generated share matrix has height and width
   exactly double those of the input matrix (2M x 2N spatial expansion).

3. Additional regression tests cover reconstruction correctness,
   contrast behaviour, secrecy of individual shares, and input
   validation guards.

Run with:
    python -m unittest test_cryptography -v
"""

from __future__ import annotations

import math
import unittest

import numpy as np

from core_engine import (
    C0_BASIS,
    C1_PAIRS,
    VisualSecretSharingEngine,
)


def compute_shannon_entropy(bit_array: np.ndarray) -> float:
    """
    Compute the exact Shannon Entropy (bits/symbol) of a binary array.

    H(X) = -sum over x in {0,1} of p(x) * log2(p(x))

    Args:
        bit_array: Flattened binary numpy array containing only 0s and 1s.

    Returns:
        The Shannon Entropy in bits, in the closed interval [0.0, 1.0].
    """
    flat: np.ndarray = np.asarray(bit_array, dtype=np.uint8).ravel()
    total_count: int = flat.size
    ones_count: int = int(np.count_nonzero(flat))
    zeros_count: int = total_count - ones_count

    entropy: float = 0.0
    for frequency in (zeros_count, ones_count):
        if frequency > 0:
            probability: float = frequency / total_count
            entropy -= probability * math.log2(probability)
    return entropy


class TestShannonEntropyBounds(unittest.TestCase):
    """Verify perfect secrecy via exact Shannon Entropy measurement."""

    def setUp(self) -> None:
        """Instantiate a fresh engine for every test case."""
        self.engine: VisualSecretSharingEngine = VisualSecretSharingEngine()

    def _build_structured_geometric_image(self) -> np.ndarray:
        """
        Construct a highly structured geometric test image.

        The pattern consists of a solid white background carrying two
        hard-edged geometric primitives: a thick black rectangular
        frame and a solid black central diamond. The composition is
        maximally structured (low native Shannon entropy, strongly
        non-uniform pixel frequencies) so that ANY leakage of the
        secret's structure into an individual share would shift the
        sub-pixel frequency distribution away from uniformity and be
        statistically detectable by the entropy assertion.

        Returns:
            A 64x64 uint8 grayscale array with extreme structure.
        """
        size: int = 64
        grid_rows, grid_cols = np.mgrid[0:size, 0:size]

        # Primitive 1: thick black rectangular frame (4 px border width).
        border_mask: np.ndarray = (
            (grid_rows < 4)
            | (grid_rows >= size - 4)
            | (grid_cols < 4)
            | (grid_cols >= size - 4)
        )

        # Primitive 2: solid black central diamond (Manhattan radius 10).
        manhattan_distance: np.ndarray = (
            np.abs(grid_rows - size // 2) + np.abs(grid_cols - size // 2)
        )
        diamond_mask: np.ndarray = manhattan_distance <= 10

        # Composite: white background (255) with black geometry (0).
        combined: np.ndarray = np.where(
            border_mask | diamond_mask, 0, 255
        ).astype(np.uint8)
        return combined

    def test_shannon_entropy_bounds(self) -> None:
        """
        Assert that both flattened shares exhibit H = 1.0 exactly.

        A highly structured geometric image is encrypted; the resulting
        share arrays are flattened and their sub-pixel frequencies are
        fed into the exact Shannon Entropy formula. Perfect secrecy
        demands H = 1.0 within a very tight tolerance margin.
        """
        structured_image: np.ndarray = self._build_structured_geometric_image()

        # Sanity check: the SOURCE is highly structured (low entropy).
        source_entropy: float = compute_shannon_entropy(structured_image)
        self.assertLess(
            source_entropy,
            0.95,
            "Test fixture error: source image should be highly structured.",
        )

        # Binarize and encrypt.
        gf2_secret: np.ndarray = self.engine.binarize_array(structured_image)
        share1, share2 = self.engine.encrypt(gf2_secret)

        # Flatten the generated output share arrays.
        flat_share1: np.ndarray = share1.ravel()
        flat_share2: np.ndarray = share2.ravel()

        # Exact Shannon Entropy via math.log2 and frequency counts.
        entropy_share1: float = compute_shannon_entropy(flat_share1)
        entropy_share2: float = compute_shannon_entropy(flat_share2)

        # Tight tolerance margin verifying zero data leakage.
        tolerance: float = 1e-9
        self.assertAlmostEqual(
            entropy_share1,
            1.0,
            delta=tolerance,
            msg=f"Share 1 entropy {entropy_share1!r} deviates from perfect H=1.0.",
        )
        self.assertAlmostEqual(
            entropy_share2,
            1.0,
            delta=tolerance,
            msg=f"Share 2 entropy {entropy_share2!r} deviates from perfect H=1.0.",
        )


class TestMatrixSpatialExpansionDimensions(unittest.TestCase):
    """Verify the 2M x 2N spatial expansion constraint."""

    def setUp(self) -> None:
        """Instantiate a fresh engine for every test case."""
        self.engine: VisualSecretSharingEngine = VisualSecretSharingEngine()

    def test_matrix_spatial_expansion_dimensions(self) -> None:
        """
        Assert that share heights and widths are exactly double the input.

        For an input matrix of shape (M, N), each generated share must
        have shape exactly (2M, 2N) per the m = 4 pixel expansion of the
        Naor-Shamir 2x2 scheme.
        """
        test_cases = [
            (16, 16),
            (17, 23),   # non-square asymmetric case
            (1, 1),     # minimal single-pixel case
            (32, 8),    # wide aspect ratio
            (5, 40),    # tall aspect ratio
        ]

        for rows, cols in test_cases:
            with self.subTest(shape=(rows, cols)):
                synthetic_input: np.ndarray = np.random.randint(
                    0, 256, size=(rows, cols), dtype=np.uint8
                )
                gf2_secret: np.ndarray = self.engine.binarize_array(synthetic_input)
                share1, share2 = self.engine.encrypt(gf2_secret)

                expected_shape: tuple[int, int] = (rows * 2, cols * 2)
                self.assertEqual(
                    share1.shape,
                    expected_shape,
                    f"Share 1 shape {share1.shape} != expected {expected_shape}.",
                )
                self.assertEqual(
                    share2.shape,
                    expected_shape,
                    f"Share 2 shape {share2.shape} != expected {expected_shape}.",
                )


class TestReconstructionCorrectness(unittest.TestCase):
    """Verify semantic correctness of the overlay reconstruction."""

    def setUp(self) -> None:
        """Instantiate a fresh engine for every test case."""
        self.engine: VisualSecretSharingEngine = VisualSecretSharingEngine()

    def test_black_pixels_reconstruct_fully_opaque(self) -> None:
        """Black secret pixels (1) must reconstruct to all-black 2x2 blocks."""
        secret: np.ndarray = np.ones((10, 10), dtype=np.uint8)
        share1, share2 = self.engine.encrypt(secret)
        reconstructed: np.ndarray = self.engine.decrypt(share1, share2)

        self.assertTrue(
            np.all(reconstructed == 1),
            "Black secret regions must reconstruct to fully opaque blocks.",
        )

    def test_white_pixels_reconstruct_at_half_transmission(self) -> None:
        """White secret pixels (0) must reconstruct to exactly 2/4 black sub-pixels."""
        secret: np.ndarray = np.zeros((12, 12), dtype=np.uint8)
        share1, share2 = self.engine.encrypt(secret)
        reconstructed: np.ndarray = self.engine.decrypt(share1, share2)

        block_sums: np.ndarray = reconstructed.reshape(12, 2, 12, 2).sum(axis=(1, 3))
        self.assertTrue(
            np.all(block_sums == 2),
            "Each white 2x2 reconstructed block must contain exactly 2 black sub-pixels.",
        )

    def test_reconstruction_preserves_secret_topology(self) -> None:
        """Block-level classification of the reconstruction must match the secret."""
        rng = np.random.default_rng(seed=42)
        secret: np.ndarray = rng.integers(0, 2, size=(20, 20)).astype(np.uint8)
        share1, share2 = self.engine.encrypt(secret)
        reconstructed: np.ndarray = self.engine.decrypt(share1, share2)

        block_sums: np.ndarray = reconstructed.reshape(20, 2, 20, 2).sum(axis=(1, 3))
        recovered_black: np.ndarray = (block_sums == 4).astype(np.uint8)

        np.testing.assert_array_equal(
            recovered_black,
            secret,
            err_msg="Recovered black-block classification must equal the secret.",
        )


class TestIndividualShareSecrecy(unittest.TestCase):
    """Verify that individual shares leak no structural information."""

    def setUp(self) -> None:
        """Instantiate a fresh engine for every test case."""
        self.engine: VisualSecretSharingEngine = VisualSecretSharingEngine()

    def test_individual_share_block_weights_are_uniform(self) -> None:
        """
        Every 2x2 block of an individual share must contain exactly 2
        black sub-pixels, regardless of whether the secret pixel was
        black or white. Hence block weight carries zero information.
        """
        secret: np.ndarray = np.zeros((15, 15), dtype=np.uint8)
        secret[::2, ::2] = 1  # interleave black and white secret pixels

        share1, share2 = self.engine.encrypt(secret)

        for share in (share1, share2):
            block_sums: np.ndarray = share.reshape(15, 2, 15, 2).sum(axis=(1, 3))
            self.assertTrue(
                np.all(block_sums == 2),
                "Every individual-share 2x2 block must weigh exactly 2.",
            )

    def test_white_blocks_are_linearly_dependent_black_independent(self) -> None:
        """
        Structural property of the basis assignment policy.

        WHITE pixels (0): the two share blocks drawn from C_0 must be
        LINEARLY DEPENDENT — identical over GF(2), i.e. one is the
        lambda = 1 scalar multiple of the other — so their physical
        overlay reproduces exactly 2 of 4 black sub-pixels (50% grey).

        BLACK pixels (1): the paired blocks drawn from C_1 must be
        LINEARLY INDEPENDENT — distinct complementary patterns whose
        rows span GF(2)^2 — so their overlay saturates at 4 of 4 black
        sub-pixels (fully opaque).
        """
        # White construction: repeated engine draws must always assign
        # IDENTICAL (linearly dependent) blocks to both shares.
        for _ in range(200):
            white_block1, white_block2 = self.engine._select_basis_block(0)
            np.testing.assert_array_equal(
                white_block1,
                white_block2,
                err_msg=(
                    "White-pixel share blocks must be identical "
                    "(linearly dependent over GF(2))."
                ),
            )
            self.assertEqual(
                int(white_block1.sum()),
                2,
                "Every C_0 block must weigh exactly 2 (one black per column pair).",
            )

        # Black construction: repeated engine draws must always assign
        # DISTINCT (linearly independent) complementary blocks whose
        # overlay saturates completely.
        for _ in range(200):
            black_block1, black_block2 = self.engine._select_basis_block(1)
            self.assertFalse(
                np.array_equal(black_block1, black_block2),
                "Black-pixel share blocks must be distinct (linearly independent).",
            )
            # Linear independence is a property of the PAIR, not of each
            # block in isolation: stacking both blocks must span rank 2
            # (e.g. the vertical pair [[1,0],[1,0]] / [[0,1],[0,1]] has
            # rank-1 members but a rank-2 union).
            stacked_pair: np.ndarray = np.vstack(
                [black_block1, black_block2]
            ).astype(np.int64)
            self.assertEqual(
                int(np.linalg.matrix_rank(stacked_pair)),
                2,
                "Each C_1 complementary pair must jointly span rank 2.",
            )
            self.assertEqual(
                int(np.maximum(black_block1, black_block2).sum()),
                4,
                "Overlay of a C_1 complementary pair must saturate at weight 4.",
            )

        # Static container sanity: C_0 holds exactly 4 candidate blocks
        # and C_1 holds exactly 4 ORDERED complementary pairs.
        self.assertEqual(C0_BASIS.shape, (4, 2, 2))
        self.assertEqual(C1_PAIRS.shape, (4, 2, 2, 2))

        # Every ordered C_1 pair must consist of completely inverted
        # (complementary) blocks whose overlay saturates at weight 4.
        ones_block: np.ndarray = np.ones((2, 2), dtype=np.uint8)
        for pair_index in range(C1_PAIRS.shape[0]):
            left_block: np.ndarray = C1_PAIRS[pair_index, 0]
            right_block: np.ndarray = C1_PAIRS[pair_index, 1]
            np.testing.assert_array_equal(
                np.maximum(left_block, right_block),
                ones_block,
                err_msg=(
                    f"C_1 pair {pair_index} must be complementary "
                    "(overlay saturates to all-black)."
                ),
            )


class TestInputValidation(unittest.TestCase):
    """Verify defensive validation guards."""

    def setUp(self) -> None:
        """Instantiate a fresh engine for every test case."""
        self.engine: VisualSecretSharingEngine = VisualSecretSharingEngine()

    def test_invalid_secret_bit_raises(self) -> None:
        """Non-binary secret bits must raise ValueError."""
        with self.assertRaises(ValueError):
            self.engine._select_basis_block(7)

    def test_non_2d_secret_raises(self) -> None:
        """Encryption of a non-2D matrix must raise ValueError."""
        with self.assertRaises(ValueError):
            self.engine.encrypt(np.zeros((4, 4, 3), dtype=np.uint8))

    def test_mismatched_share_shapes_raise_on_decrypt(self) -> None:
        """Decrypting mismatched share shapes must raise ValueError."""
        with self.assertRaises(ValueError):
            self.engine.decrypt(np.zeros((4, 4)), np.zeros((6, 6)))

    def test_non_binary_render_input_raises(self) -> None:
        """Rendering a non-binary matrix to PNG must raise ValueError."""
        with self.assertRaises(ValueError):
            self.engine.binary_to_png_bytes(np.array([[0, 1], [2, 3]]))


if __name__ == "__main__":
    unittest.main(verbosity=2)