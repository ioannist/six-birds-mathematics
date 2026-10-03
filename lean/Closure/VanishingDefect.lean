import Mathlib.Topology.MetricSpace.Basic
import Mathlib.Topology.Algebra.Order.Field

/-! A concrete packaging contract: vanishing pseudometric distance is an
equivalence relation. Arbitrary nonnegative diagnostics need not be. -/

namespace Closure

open Filter

variable (X : Type*) [PseudoMetricSpace X]

/-- The comparison space and its pseudometric are part of the contract. This
quotient does not claim that every sequence converges or that it is a completion. -/
def vanishingDistSetoid : Setoid (ℕ → X) where
  r a b := Tendsto (fun n => dist (a n) (b n)) atTop (nhds 0)
  iseqv := {
    refl := fun a => by simp
    symm := fun hab => by simpa only [dist_comm] using hab
    trans := fun hab hbc => by
      have hsum := hab.add hbc
      exact squeeze_zero (fun n => dist_nonneg)
        (fun n => dist_triangle _ _ _) (by simpa only [zero_add] using hsum)
  }

variable {X} {Y : Type*} [PseudoMetricSpace Y]

/-- A uniform Lipschitz estimate supplies descent; naming a micro-operator alone
does not. The operator may depend on the stage. -/
theorem stage_operator_respects_vanishing_dist
    {F : ℕ → X → Y} {K : ℝ} (_hK : 0 ≤ K)
    (hF : ∀ n x y, dist (F n x) (F n y) ≤ K * dist x y)
    {a b : ℕ → X} (hab : (vanishingDistSetoid X).r a b) :
    (vanishingDistSetoid Y).r (fun n => F n (a n)) (fun n => F n (b n)) := by
  have hconst : Tendsto (fun _ : ℕ => K) atTop (nhds K) := tendsto_const_nhds
  have hbound := hconst.mul hab
  exact squeeze_zero (fun n => dist_nonneg) (fun n => hF n _ _)
    (by simpa only [mul_zero] using hbound)

end Closure
