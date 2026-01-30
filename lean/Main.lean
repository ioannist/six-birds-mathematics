import Mathlib
import Derivations.Polynomial
import Diff.FiniteDifference

#check Derivation
#check Polynomial.derivative
#check Diff.delta_mul_leibniz
#check Derivations.polynomialDerivationEquiv_apply_X
#check Derivations.polynomialDerivationEquiv_symm_apply_X

lemma sanity_nat : (2:Nat) + 2 = 4 := by
  decide
