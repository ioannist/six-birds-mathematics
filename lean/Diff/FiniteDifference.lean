import Mathlib

namespace Diff

variable {F : Type*} [Field F]

/-- Scaled forward difference. -/ 
def delta (h : F) (f : F → F) (x : F) : F :=
  (f (x + h) - f x) / h

/-- Discrete Leibniz identity with remainder term. -/
theorem delta_mul_leibniz (h : F) (h0 : h ≠ 0) (f g : F → F) (x : F) :
    delta h (fun y => f y * g y) x
      = delta h f x * g x
        + f x * delta h g x
        + h * delta h f x * delta h g x := by
  unfold delta
  field_simp [h0]
  ring

end Diff
