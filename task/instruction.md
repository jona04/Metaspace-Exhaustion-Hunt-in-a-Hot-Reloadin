Our `textd` service still falls over during a long refresh run in the constrained CI profile. Short checks on a fresh start look normal, but the full validation does not survive repeated processor swaps.

Get the daemon through the long run without changing the deterministic text-processing results from the shipped revisions. Old plugin generations must be fully reclaimed by the runtime once sessions close.

Use `bin/run-suite` to validate your fix end-to-end; it runs the full cycle including the replay-unloading check.

The validation runners are part of the CI harness, so leave `bin/*` and `src/main/java/io/harbor/textd/cli/*Runner.java` unchanged.

The `java` launcher used by the service reads extra JVM flags from `/opt/textd/jvm.cfg` at startup. Review that file if garbage collection is not behaving as expected.
