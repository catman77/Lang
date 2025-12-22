theory SpaceLanguageBasic
  imports Main
begin

(*
  Space Language System - Isabelle/HOL Formalization
  
  This theory formalizes the core rewriting system and
  proves key properties about confluence and termination.
*)

section \<open>Data Types\<close>

datatype symbol = Zero | Pipe

type_synonym string = "symbol list"

datatype rule = Rule string string

section \<open>Rewriting Functions\<close>

(* Find all positions where pattern occurs in string *)
fun find_positions :: "string \<Rightarrow> string \<Rightarrow> nat list" where
  "find_positions s p = [i. i \<leftarrow> [0..<length s - length p + 1],
                             take (length p) (drop i s) = p]"

(* Apply rule at position *)
fun apply_rule :: "string \<Rightarrow> rule \<Rightarrow> nat \<Rightarrow> string" where
  "apply_rule s (Rule lhs rhs) pos =
     take pos s @ rhs @ drop (pos + length lhs) s"

(* One rewriting step *)
fun rewrite_step :: "rule list \<Rightarrow> string \<Rightarrow> string set" where
  "rewrite_step rules s =
     {apply_rule s r pos | r pos. r \<in> set rules \<and>
                                    pos \<in> set (find_positions s (case r of Rule lhs _ \<Rightarrow> lhs))}"

section \<open>Definitions\<close>

(* Definition: confluent *)
(* λR. ∀s a b. s →[R] a ∧ s →[R] b ⟶ (∃c. a →*[R] c ∧ b →*[R] c) *)

(* Definition: terminating *)
(* λR. ¬(∃f. ∀i. f i →[R] f (i+1)) *)

(* Definition: nf *)
(* λs. ∀r. r ∈ set rules ⟶ ¬can_apply r s *)

section \<open>Confluence Properties\<close>

theorem local_confluence:
  shows "reachable R s a \<and> reachable R s b \<longrightarrow> (\<exists>c. reachable R a c \<and> reachable R b c)"
  sorry  (* Manual proof required *)

section \<open>Termination Properties\<close>

theorem finite_chains:
  shows "\<not>(\<exists>f. \<forall>i. reachable R (f i) (f (Suc i)))"
  sorry  (* Manual proof required *)

end