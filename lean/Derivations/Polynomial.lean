import Mathlib.Algebra.Polynomial.Derivation

noncomputable section

namespace Derivations

variable {R : Type*} [CommSemiring R]

/-- Derivations on `R[X]` are determined by their value on `X`. -/
theorem derivation_ext_X
    {D₁ D₂ : Derivation R (Polynomial R) (Polynomial R)}
    (hX : D₁ Polynomial.X = D₂ Polynomial.X) : D₁ = D₂ := by
  simpa using (Polynomial.derivation_ext (R:=R) (A:=Polynomial R) hX)

/-- `Derivation R R[X] R[X] ≃ₗ[R] R[X]` via `D ↦ D X`. -/
def polynomialDerivationEquiv (R : Type*) [CommSemiring R] :
    Derivation R (Polynomial R) (Polynomial R) ≃ₗ[R] Polynomial R :=
  (Polynomial.mkDerivationEquiv (R:=R) (A:=Polynomial R)).symm

@[simp] theorem polynomialDerivationEquiv_apply_X
    (D : Derivation R (Polynomial R) (Polynomial R)) :
    polynomialDerivationEquiv R D = D Polynomial.X := by
  simp [polynomialDerivationEquiv]

@[simp] theorem polynomialDerivationEquiv_symm_apply_X
    (p : Polynomial R) :
    (polynomialDerivationEquiv R).symm p Polynomial.X = p := by
  simp [polynomialDerivationEquiv]

/-- The inverse equivalence really is multiplication by the formal derivative. -/
theorem polynomialDerivationEquiv_symm_apply
    (p q : Polynomial R) :
    (polynomialDerivationEquiv R).symm p q = p * Polynomial.derivative q := by
  simp [polynomialDerivationEquiv, Polynomial.mkDerivation_apply, smul_eq_mul, mul_comm]

/-- The usual formal derivative is the normalized derivation, over any commutative semiring. -/
theorem derivation_eq_derivative_of_X_eq_one
    (D : Derivation R (Polynomial R) (Polynomial R)) (hX : D Polynomial.X = 1)
    (q : Polynomial R) : D q = Polynomial.derivative q := by
  have hD : D = (polynomialDerivationEquiv R).symm 1 := by
    apply derivation_ext_X
    simpa using hX
  rw [hD, polynomialDerivationEquiv_symm_apply, one_mul]

end Derivations
