import Lake
open Lake DSL

package sbt_math

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.9.1"

lean_lib SbtMath where
  srcDir := "."
  roots := #[`Derivations.Polynomial, `Diff.FiniteDifference]

@[default_target]
lean_exe sbt_math where
  root := `Main
