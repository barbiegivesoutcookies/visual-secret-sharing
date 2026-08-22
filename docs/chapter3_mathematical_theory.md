# Chapter 3: Mathematical Theory & Formal Proofs

## 3.1 Introduction

This chapter establishes the complete mathematical foundation of the
Matrix-Based Visual Secret Sharing system implemented in this project. We
formally define the computational domain as the finite field GF(2), present
the exact basis matrix sets of the Naor-Shamir (2,2) Threshold Visual
Cryptography Scheme, prove — via a step-by-step application of Bayes'
Theorem — that the scheme achieves **perfect secrecy**, and rigorously
evaluate the **contrast function**, demonstrating the inherent 50% geometric
light transmission loss.

Throughout this chapter, we adopt the following notation:

| Symbol | Meaning |
|---|---|
| $X$ | The secret random variable (a single binary pixel), $\{0,1\}$-valued |
| $S_1, S_2$ | The two generated share random variables ($2\times2$ blocks per pixel) |
| $R$ | The reconstructed (stacked) random variable |
| $m$ | Pixel expansion factor ($m = 4$ for the 2×2 scheme) |
| $C_0, C_1$ | Basis collections for white and black secret pixels |
| $w(\cdot)$ | Hamming weight (number of black sub-pixels) |
| $H(\cdot)$ | Shannon Entropy function |
| $P(\cdot \mid \cdot)$ | Conditional probability |

---

## 3.2 The Finite Field GF(2)

### 3.2.1 Field Definition

**Definition 3.1 (Finite Field GF(2)).**
The Galois Field of order 2, denoted $\mathrm{GF}(2)$, is the algebraic
structure

$$
\mathrm{GF}(2) = (\{0, 1\}, \oplus, \otimes)
$$

where the two binary operations are defined by the following tables:

**Addition ($\oplus$, XOR):**

| $\oplus$ | 0 | 1 |
|---|---|---|
| **0** | 0 | 1 |
| **1** | 1 | 0 |

**Multiplication ($\otimes$, AND):**

| $\otimes$ | 0 | 1 |
|---|---|---|
| **0** | 0 | 0 |
| **1** | 1 | 1 |

**Proposition 3.1.** $(\{0,1\}, \oplus, \otimes)$ satisfies all field axioms.

*Proof.*
1. **Associativity/Commutativity of $\oplus$:** Immediate from the truth table of XOR, which is invariant under operand permutation and association.
2. **Additive identity:** $a \oplus 0 = a$ for all $a \in \{0,1\}$; the identity element is $0$.
3. **Additive inverse:** Every element is its own inverse since $a \oplus a = 0$.
4. **Associativity/Commutativity of $\otimes$:** Immediate from the AND truth table.
5. **Multiplicative identity:** $a \otimes 1 = a$; the identity element is $1$.
6. **Distributivity:** $a \otimes (b \oplus c) = a \otimes b \oplus a \otimes c$ holds by exhaustive verification over the eight assignments of $(a,b,c) \in \{0,1\}^3$.
7. **Multiplicative inverse:** The only nonzero element is $1$, and $1 \otimes 1 = 1$; hence $1^{-1} = 1$. $\blacksquare$

### 3.2.2 Mapping Digital Images into GF(2)

**Definition 3.2 (Strict Threshold Binarization).**
Let $I: \{0,\dots,M-1\} \times \{0,\dots,N-1\} \to \{0,\dots,255\}$ be a
grayscale digital image. The GF(2) mapping $\phi: I \to B$ is defined as

$$
\phi(I)(x,y) =
\begin{cases}
0 & \text{if } I(x,y) \geq 128 \quad \text{(White / Transparent)}\\[4pt]
1 & \text{if } I(x,y) < 128 \quad \text{(Black / Opaque)}
\end{cases}
$$

The midpoint constant $128$ partitions the 8-bit intensity domain
$\{0,\dots,255\}$ into two equipotent halves of 128 values each, ensuring a
balanced, unbiased quantization boundary. In the implementation
(`core_engine.py`), this is realized as the vectorized NumPy expression:

```python
gf2_matrix = np.where(pixel_array >= 128, 0, 1).astype(np.uint8)
```

---

## 3.3 The Naor-Shamir (2,2) Threshold Scheme

### 3.3.1 Scheme Parameters

The (2,2) threshold scheme is parameterized by the tuple

$$
\Pi = (k, n, m) = (2, 2, 4)
$$

where:

- $k = 2$: the minimum number of shares required for reconstruction,
- $n = 2$: the total number of shares distributed,
- $m = 4$: the pixel expansion factor — each secret pixel becomes a $2\times2$
  block of sub-pixels on **every** share, so each share measures exactly
  $2M \times 2N$.

### 3.3.2 Exact Basis Matrix Sets

It is convenient to name the four admissible weight-2 blocks, which together
constitute the common support of both share distributions:

$$
B_1 = \begin{bmatrix} 1 & 0 \\ 1 & 0 \end{bmatrix},\quad
B_2 = \begin{bmatrix} 0 & 1 \\ 0 & 1 \end{bmatrix},\quad
B_3 = \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix},\quad
B_4 = \begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}
$$

Note that $B_2, B_4$ are the column transpositions of $B_1, B_3$
respectively, and that every $B_i$ carries exactly one black sub-pixel in
each column.

**Definition 3.3 (Basis Collection $C_0$ — White Pixels).**
For a white ($X = 0$) secret pixel, ONE block is drawn uniformly from $C_0$
and the **identical** block is assigned to both shares:

$$
C_0 = \left\{
\begin{bmatrix} 1 & 0 \\ 1 & 0 \end{bmatrix},
\begin{bmatrix} 0 & 1 \\ 0 & 1 \end{bmatrix},
\begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix},
\begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}
\right\} = \{B_1, B_2, B_3, B_4\}
$$

Because each column of every $C_0$ member contains exactly one black
sub-pixel, overlaying two identical copies reproduces exactly $2$ of $4$
black sub-pixels — the reconstructed white region appears as a uniform
mid-grey checkerboard.

**Definition 3.4 (Basis Collection $C_1$ — Black Pixels).**
For a black ($X = 1$) secret pixel, ONE **ordered complementary pair** is
drawn uniformly from $C_1$ and split across the two shares:

$$
C_1 = \left\{
\left(
\begin{bmatrix} 1 & 0 \\ 1 & 0 \end{bmatrix},
\begin{bmatrix} 0 & 1 \\ 0 & 1 \end{bmatrix}
\right),
\left(
\begin{bmatrix} 0 & 1 \\ 0 & 1 \end{bmatrix},
\begin{bmatrix} 1 & 0 \\ 1 & 0 \end{bmatrix}
\right),
\left(
\begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix},
\begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}
\right),
\left(
\begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix},
\begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}
\right)
\right\}
$$

$$
= \{(B_1, B_2),\ (B_2, B_1),\ (B_3, B_4),\ (B_4, B_3)\}
$$

Each pair consists of **completely inverted** (complementary) blocks whose
rows are linearly independent as a set — jointly spanning
$\mathrm{GF}(2)^2$ — so the physical overlay reproduces $4$ of $4$ black
sub-pixels: the reconstructed black region is fully opaque.

**Structural Observation 3.1.**

1. Every emitted block — from either collection — has Hamming weight exactly
   $w(B_i) = 2$. Consequently, *every* $2\times2$ block of *every*
   individual share weighs exactly 2, regardless of the underlying secret.
2. In the white construction the two assigned blocks are identical, hence
   linearly dependent over GF(2) (one is the $\lambda = 1$ scalar multiple
   of the other).
3. In the black construction the two assigned blocks are complements;
   although an individual member such as $B_1$ has rank-1 rows, the stacked
   pair $\{B_i, \bar{B_i}\}$ always spans rank 2 over GF(2).
4. The four ordered pairs of $C_1$ are carefully enumerated so that the
   marginal distribution of Share 1's block given $X = 1$ is *exactly* the
   uniform distribution over $\{B_1,B_2,B_3,B_4\}$ — the same distribution
   as given $X = 0$. This symmetry is the load-bearing pillar of the secrecy
   proof in Section 3.4.

### 3.3.3 Uniform Random Selection Mechanism

For each secret pixel, the engine composes two independent draws of a true
uniform random bit selector,

$$
j, k \sim \mathrm{Uniform}\{0, 1\}, \qquad u = 2j + k \in \{0,1,2,3\},
$$

implemented with `random.randint(0, 1)` as the base primitive. The index $u$
selects the configuration uniformly from the relevant collection. Because
the selection is independent of $X$ and uniformly distributed, and because
every admissible block has weight 2, each individual share's sub-pixel
process is an i.i.d. Bernoulli($\tfrac{1}{2}$) ensemble at every position.

---

## 3.4 Perfect Secrecy: A Step-by-Step Bayes' Theorem Proof

**Theorem 3.1 (Perfect Secrecy).**
For the Naor-Shamir (2,2) scheme as implemented,

$$
P(X = x \mid S_1 = s_1) = P(X = x) \quad \forall\, x \in \{0,1\},\ \forall\, s_1 \in \mathcal{B}
$$

where $\mathcal{B} = \{B_1, B_2, B_3, B_4\}$. That is, observing an entire
share block provides zero information about the secret pixel.

*Proof.* We proceed step by step.

**Step 1 — Enumerate the admissible block set.**
By Definitions 3.3 and 3.4, the only possible emitted blocks for Share 1
are:

$$
\mathcal{B} = \left\{
\begin{bmatrix} 1 & 0 \\ 1 & 0 \end{bmatrix},
\begin{bmatrix} 0 & 1 \\ 0 & 1 \end{bmatrix},
\begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix},
\begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}
\right\} = \{B_1, B_2, B_3, B_4\}
$$

**Step 2 — Compute the conditional emission probabilities given the secret.**

If $X = 0$ (white), the uniform index $u \in \{0,1,2,3\}$ selects directly
among the four members of $C_0$:

$$
P(S_1 = B_i \mid X = 0) = \tfrac{1}{4} \qquad \forall\, i \in \{1,2,3,4\}
$$

If $X = 1$ (black), the same uniform index selects among the four **ordered
pairs** of $C_1$, and Share 1 receives the first component of the selected
pair. Reading off the first components of
$(B_1,B_2), (B_2,B_1), (B_3,B_4), (B_4,B_3)$ yields $(B_1, B_2, B_3, B_4)$
— each value attained by exactly one pair:

$$
P(S_1 = B_i \mid X = 1) = \tfrac{1}{4} \qquad \forall\, i \in \{1,2,3,4\}
$$

This is the decisive property of the ordered-pair enumeration: the
conditional distribution of Share 1's block is **identical under both
secret values**.

**Step 3 — Apply the Law of Total Probability.**
For an arbitrary prior $\pi_0 = P(X=0)$, $\pi_1 = P(X=1)$:

$$
P(S_1 = B_i) = P(S_1 = B_i \mid X = 0)\,\pi_0 + P(S_1 = B_i \mid X = 1)\,\pi_1 = \tfrac{1}{4}\pi_0 + \tfrac{1}{4}\pi_1 = \tfrac{1}{4}
$$

for every $i \in \{1,2,3,4\}$. Hence $S_1$ is uniformly distributed over
$\mathcal{B}$ **regardless of the prior on $X$** — no assumption about the
natural-image statistics is required.

**Step 4 — Apply Bayes' Theorem.**
Bayes' Theorem states:

$$
P(X = x \mid S_1 = s_1) = \frac{P(S_1 = s_1 \mid X = x)\, P(X = x)}{P(S_1 = s_1)}
$$

Substituting the results of Steps 2 and 3 for any $x \in \{0,1\}$ and any
$s_1 = B_i$:

$$
P(X = x \mid S_1 = B_i) = \frac{\tfrac{1}{4} \cdot P(X = x)}{\tfrac{1}{4}} = P(X = x)
$$

The posterior equals the prior exactly, for every observable block and every
prior. Since consecutive pixels are encrypted with independent random draws,
the joint distribution of the entire share matrix factorizes into a product
of identical block marginals, and the argument extends verbatim from a
single block to the full $2M \times 2N$ observation:

$$
P(X^{(M\times N)} = \xi \mid S_1 = \sigma) = P(X^{(M\times N)} = \xi)
\qquad \blacksquare
$$

**Corollary 3.1 (Shannon Entropy of Individual Shares).**
Since each sub-pixel of each share is an i.i.d. Bernoulli($\tfrac12$)
variable,

$$
H(S_1) = H(S_2) = -\sum_{s \in \{0,1\}} \tfrac{1}{2}\log_2 \tfrac{1}{2} = 1.0 \ \text{bit per sub-pixel}
$$

and the mutual information vanishes:

$$
I(X; S_1) = H(X) - H(X \mid S_1) = H(X) - H(X) = 0
$$

A useful deterministic reinforcement: because every emitted block weighs
exactly 2, a share of $M \times N$ secret pixels contains *exactly*
$2MN$ black sub-pixels out of $4MN$ total — the empirical frequency count
is balanced by construction, not merely in expectation. This corollary is
enforced empirically by the automated test `test_shannon_entropy_bounds`
in `test_cryptography.py`, which asserts $H = 1.0$ within a $10^{-9}$
tolerance.

---

## 3.5 Contrast Function Evaluation: The 50% Transmission Loss

**Definition 3.5 (Reconstruction Operator).**
Physical transparency stacking corresponds to the logical OR of aligned
sub-pixels. For share blocks $S_1^{(ij)}, S_2^{(ij)}$:

$$
R^{(ij)} = S_1^{(ij)} \lor S_2^{(ij)}
$$

implemented in optimized vectorized form as `np.maximum(share1, share2)`.

**Definition 3.6 (Relative Contrast).**
Following Naor and Shamir (1994), the relative contrast of the scheme is

$$
\alpha = \frac{w(R \mid X = 1) - w(R \mid X = 0)}{m}
$$

where $w(\cdot)$ denotes the Hamming weight of the stacked block and
$m = 4$ is the expansion factor.

**Evaluation for $X = 1$ (black secret pixel).**
Share 1 receives some $B_i$ and Share 2 receives its complement $\bar{B_i}$.
Stacking, e.g. for $i = 3$:

$$
\begin{bmatrix}1&0\\0&1\end{bmatrix} \lor \begin{bmatrix}0&1\\1&0\end{bmatrix} = \begin{bmatrix}1&1\\1&1\end{bmatrix}
$$

Hence $w(R \mid X = 1) = 4$ deterministically — the reconstructed region is
**fully black** (0% light transmission).

**Evaluation for $X = 0$ (white secret pixel).**
Both shares receive the *same* block $B_i$. Stacking a block with itself
reproduces the block unchanged:

$$
B_i \lor B_i = B_i, \qquad w(B_i) = 2 \ \ \forall i
$$

Hence $w(R \mid X = 0) = 2$ deterministically — exactly **two** of the four
stacked sub-pixels are black and two are transparent, so the reconstructed
region transmits exactly **50% of incident light**, appearing as a uniform
mid-grey.

**Contrast Computation.**

$$
\alpha = \frac{w(R \mid X = 1) - w(R \mid X = 0)}{m} = \frac{4 - 2}{4} = \frac{1}{2}
$$

Equivalently, the average light transmission of reconstructed white regions
is $T_0 = w(R \mid X = 0)/m = 2/4 = 50\%$, while reconstructed black regions
transmit $T_1 = 0\%$. The perceptual difference between the two states is
therefore maximal at the block level even though the absolute brightness of
white regions is halved.

**Theorem 3.2 (Geometric Light Transmission Loss).**
The scheme exhibits an irreducible 50% geometric light transmission loss on
white regions: a source area that transmitted 100% of light now transmits
exactly 50%, because half of the $m = 4$ sub-pixels per block are consumed
by black mask dots required to preserve secrecy.

*Proof.* By the secrecy constraint (Theorem 3.1), each individual share must
carry exactly 2 black sub-pixels per block regardless of $X$ — any other
weight would immediately distinguish the secret value. Upon OR-stacking two
such blocks, the stacked weight for a white pixel is bounded below by the
weight of either share alone:

$$
w(R \mid X = 0) \geq \max\big(w(S_1), w(S_2)\big) = 2
$$

The implemented identical-block assignment attains this lower bound exactly,
$w(R \mid X = 0) = 2$, hence transmission
$T_0 = (m - w)/m = (4-2)/4 = 50\%$. Any reduction of this loss would require
either $w(R \mid X = 0) < 2$ — impossible under the weight-2 secrecy
constraint — or a smaller expansion factor $m < 4$, which violates the
combinatorial feasibility conditions established by Naor and Shamir (1994)
for the (2,2) threshold. $\blacksquare$

**Corollary 3.2 (Contrast Constraint).**
The reconstructed image is always legible — black regions at 0%
transmission, white regions at exactly 50% — but never exceeds 50%
brightness in formerly-white areas. This is a fundamental, provable
trade-off between secrecy and visual fidelity, not an engineering
deficiency.

---

## 3.6 Summary

This chapter established:

1. The computational domain $\mathrm{GF}(2)$ and its axiomatic completeness (Proposition 3.1).
2. The strict midpoint-128 binarization map $\phi$ (Definition 3.2).
3. The exact basis collections: $C_0 = \{B_1,B_2,B_3,B_4\}$ with identical-block assignment, and $C_1$ as four ordered complementary pairs, with their rank-theoretic distinction (Definitions 3.3–3.4, Observation 3.1).
4. A step-by-step Bayes' Theorem proof that $P(X = x \mid S_1 = s_1) = P(X = x)$ — exact for every prior — establishing perfect secrecy with $H(S_i) = 1.0$ and $I(X; S_i) = 0$ (Theorem 3.1, Corollary 3.1).
5. A rigorous contrast evaluation proving the deterministic stacked weights $w(R|X{=}1)=4$ and $w(R|X{=}0)=2$, yielding relative contrast $\alpha = 1/2$ and the irreducible 50% geometric light transmission loss on white regions (Theorem 3.2, Corollary 3.2).

Chapter 4 builds upon these foundations to analyze the algorithmic time and
space complexity of the reference implementation.