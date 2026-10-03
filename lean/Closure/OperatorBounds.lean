import Mathlib.Analysis.NormedSpace.OperatorNorm.Basic

/-! Correct scope for the background paper's perturbation toolkit: continuous
linear maps. The factorization is false for arbitrary nonlinear maps. -/

namespace Closure

variable {𝕜 E F G : Type*} [NontriviallyNormedField 𝕜]
  [NormedAddCommGroup E] [NormedAddCommGroup F] [NormedAddCommGroup G]
  [NormedSpace 𝕜 E] [NormedSpace 𝕜 F] [NormedSpace 𝕜 G]

/-- The route defect contributes additively to the norm gain bound. -/
theorem route_gain_bound (A : F →L[𝕜] G) (B : E →L[𝕜] F) (C : E →L[𝕜] G) :
    ‖C‖ ≤ ‖A‖ * ‖B‖ + ‖C - A.comp B‖ := by
  calc
    ‖C‖ = ‖A.comp B + (C - A.comp B)‖ := by rw [add_comm, sub_add_cancel]
    _ ≤ ‖A.comp B‖ + ‖C - A.comp B‖ := norm_add_le _ _
    _ ≤ ‖A‖ * ‖B‖ + ‖C - A.comp B‖ :=
      add_le_add_right (A.opNorm_comp_le B) _

/-- Linearity is the substantive hypothesis behind the factorization. -/
theorem idempotence_factorization (L : E →L[𝕜] E) :
    L.comp L - L = L.comp (L - ContinuousLinearMap.id 𝕜 E) := by
  simp

theorem idempotence_defect_bound (L : E →L[𝕜] E) :
    ‖L.comp L - L‖ ≤ ‖L‖ * ‖L - ContinuousLinearMap.id 𝕜 E‖ := by
  rw [idempotence_factorization]
  exact L.opNorm_comp_le _

end Closure
