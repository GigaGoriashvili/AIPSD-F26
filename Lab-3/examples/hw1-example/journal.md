# Pattern Journal · <github-username> · Weeks 1 to 4

*Copied from `docs/journal/<github-username>.md`. One entry per week: the pattern, one place I saw or used it, one thing I would do differently.*

## Week 1 · The Autonomy Ladder (Delegation and Verification)

**Where I used it:** choosing rung 2 for the Lab 1 spec draft (the agent suggested, I typed) and rung 3 for HW1 code. **What I noticed:** at rung 3 the diff is the product; if I do not read it, I have silently moved to rung 4. **Do differently:** write the rung into the prompt so the agent knows it must stop at a plan.

## Week 2 · Spec Before Code

**Where I used it:** rewriting "returns the right events" into "returns at most three events with date >= today, sorted by date then time". **What I noticed:** the agent's first plan skipped the unknown-club case because my v0 spec did not have it; the spec was the bug, not the code. **Do differently:** write the error criteria first, they are the ones I forget.

## Week 3 · Uncertainty-Aware UX

**Where I used it:** in Lab 3 our degraded receipt photo came back with a total of 48.00 and confidence 0.91 but no evidence string; the evidence check sent it to review and the real total was 46.00. **What I noticed:** the model's confidence number told me nothing; the empty evidence field told me everything. **Do differently:** check evidence before confidence in `decide()` from the start, instead of adding it after the demo.

## Week 4 · Grounded Generation

**Where I used it:** [written after the Week 4 lecture: the first golden set for our capstone, and what retrieval with citations changed about the answers]. **What I noticed:** [ ]. **Do differently:** [ ].
