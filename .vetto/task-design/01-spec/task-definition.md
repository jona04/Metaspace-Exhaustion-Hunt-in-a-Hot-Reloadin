Our `textd` service still falls over during a long refresh run in the constrained CI profile. Short checks on a fresh start look normal, but the full validation does not survive repeated processor swaps.

Get the daemon through the long CI validation without changing the deterministic text-processing results from the shipped revisions. Do not work around the failure by raising memory limits, weakening validation, or adding explicit garbage-collection triggers to the daemon.

Use `bin/run-suite` to validate your fix end-to-end.

The validation runners are part of the CI harness, so leave `bin/*` and `src/main/java/io/harbor/textd/cli/*Runner.java` unchanged.
