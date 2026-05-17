# textd refresh soak task

This task ships a Java daemon at `/workspace/textd` that keeps swapping a customer processor jar in place while serving traffic from a fixed four-thread pool. The visible failure is a long soak under `-XX:MaxMetaspaceSize=64m`, but the repair is spread across the reload path, per-thread state, and shutdown path so it is not a one-line fix.

The plugin jar deliberately loads `PipelineStages` with 192 nested classes per revision. That makes leaked historical frames expensive enough to exhaust Metaspace during `bin/stress 500`, even though request outputs remain correct for quite a while.

The public `bin/run-suite` path is intended to match the hidden verifier closely: it builds, runs the integration and digest checks, performs the 500-cycle stress run, and runs `bin/replay-check` before printing `suite-ok`. The JVM wrapper reads `/opt/textd/jvm.cfg`, which initially disables explicit GC; a complete fix must account for that runtime config so replay unloading can be observed.

The verifier checks that the soak finishes, the functional outputs still match the shipped revisions, the sampled worker identities stay stable across four workers, the daemon still reports a clean close, a second replay in the same JVM still closes cleanly, the replay-check wrapper prints positive unloading deltas, and the public runner surfaces - including the replay runner - have not been stubbed or rewritten. The agent instruction now explicitly says those runner surfaces are CI harness files and should be left unchanged.
