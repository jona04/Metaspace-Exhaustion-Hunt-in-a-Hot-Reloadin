Our `textd` service still falls over during a long refresh run in the constrained CI profile. Short checks on a fresh start look normal, but the full validation does not survive repeated processor swaps.

Get the daemon through the long run without changing the deterministic text-processing results from the shipped revisions. Old plugin generations must be fully reclaimed by the runtime once sessions close.
