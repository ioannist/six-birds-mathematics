import Derivations.Polynomial
import Diff.FiniteDifference
import Closure.VanishingDefect
import Closure.OperatorBounds

#check Derivation
#check Polynomial.derivative
#check Diff.delta_mul_leibniz
#check Derivations.polynomialDerivationEquiv_apply_X
#check Derivations.polynomialDerivationEquiv_symm_apply_X

#print axioms Diff.delta_mul_leibniz
#print axioms Diff.delta_const
#print axioms Diff.delta_add
#print axioms Diff.delta_const_mul
#print axioms Diff.tendsto_delta_mul
#print axioms Diff.leibniz_of_tendsto_delta
#print axioms Derivations.derivation_ext_X
#print axioms Derivations.polynomialDerivationEquiv
#print axioms Derivations.polynomialDerivationEquiv_apply_X
#print axioms Derivations.polynomialDerivationEquiv_symm_apply_X
#print axioms Derivations.polynomialDerivationEquiv_symm_apply
#print axioms Derivations.derivation_eq_derivative_of_X_eq_one
#print axioms Closure.vanishingDistSetoid
#print axioms Closure.stage_operator_respects_vanishing_dist
#print axioms Closure.route_gain_bound
#print axioms Closure.idempotence_factorization
#print axioms Closure.idempotence_defect_bound

lemma sanity_nat : (2:Nat) + 2 = 4 := by
  decide
