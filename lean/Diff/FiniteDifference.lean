import Mathlib.Topology.Algebra.Order.Field
import Mathlib.Topology.Instances.Real
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace Diff

set_option autoImplicit false

variable {F : Type*} [Field F]

/-- Scaled forward difference. -/ 
def delta (h : F) (f : F → F) (x : F) : F :=
  (f (x + h) - f x) / h

/-- Linearity is required in addition to the limiting product rule. -/
theorem delta_add (h : F) (f g : F → F) (x : F) :
    delta h (fun y => f y + g y) x = delta h f x + delta h g x := by
  simp only [delta, div_eq_mul_inv]
  ring

theorem delta_const_mul (h a : F) (f : F → F) (x : F) :
    delta h (fun y => a * f y) x = a * delta h f x := by
  simp only [delta, div_eq_mul_inv]
  ring

@[simp] theorem delta_const (h a x : F) : delta h (fun _ => a) x = 0 := by
  simp [delta]

/-- Discrete Leibniz identity with remainder term. -/
theorem delta_mul_leibniz (h : F) (h0 : h ≠ 0) (f g : F → F) (x : F) :
    delta h (fun y => f y * g y) x
      = delta h f x * g x
        + f x * delta h g x
        + h * delta h f x * delta h g x := by
  unfold delta
  field_simp [h0]
  ring

/-- Given convergence of the two factor quotients, derive convergence of the
product quotient along the same filter. Boundedness alone does not supply the
factor limits; a limit along a sampled sequence need not be a full derivative. -/
theorem tendsto_delta_mul {ι : Type*} {l : Filter ι}
    {h : ι → ℝ} {f g : ℝ → ℝ} {x a b : ℝ}
    (hzero : Filter.Tendsto h l (nhds 0))
    (hnonzero : ∀ᶠ i in l, h i ≠ 0)
    (hf : Filter.Tendsto (fun i => delta (h i) f x) l (nhds a))
    (hg : Filter.Tendsto (fun i => delta (h i) g x) l (nhds b)) :
    Filter.Tendsto (fun i => delta (h i) (fun y => f y * g y) x) l
      (nhds (a * g x + f x * b)) := by
  have hc_g : Filter.Tendsto (fun _ : ι => g x) l (nhds (g x)) := tendsto_const_nhds
  have hc_f : Filter.Tendsto (fun _ : ι => f x) l (nhds (f x)) := tendsto_const_nhds
  have hr := ((hf.mul hc_g).add (hc_f.mul hg)).add
    ((hzero.mul hf).mul hg)
  have hright : Filter.Tendsto
      (fun i => delta (h i) f x * g x + f x * delta (h i) g x +
        h i * delta (h i) f x * delta (h i) g x) l (nhds (a * g x + f x * b)) := by
    simpa only [zero_mul, add_zero] using hr
  have heq : (fun i => delta (h i) (fun y => f y * g y) x) =ᶠ[l]
      (fun i => delta (h i) f x * g x + f x * delta (h i) g x +
        h i * delta (h i) f x * delta (h i) g x) :=
    hnonzero.mono (fun i hi => delta_mul_leibniz (h i) hi f g x)
  exact hright.congr' heq.symm

/-- Identification with any supplied product limit additionally needs a nontrivial
filter (otherwise every value is a limit). -/
theorem leibniz_of_tendsto_delta {ι : Type*} {l : Filter ι} [l.NeBot]
    {h : ι → ℝ} {f g : ℝ → ℝ} {x a b c : ℝ}
    (hzero : Filter.Tendsto h l (nhds 0))
    (hnonzero : ∀ᶠ i in l, h i ≠ 0)
    (hf : Filter.Tendsto (fun i => delta (h i) f x) l (nhds a))
    (hg : Filter.Tendsto (fun i => delta (h i) g x) l (nhds b))
    (hfg : Filter.Tendsto (fun i => delta (h i) (fun y => f y * g y) x) l (nhds c)) :
    c = a * g x + f x * b :=
  tendsto_nhds_unique hfg (tendsto_delta_mul hzero hnonzero hf hg)

end Diff
