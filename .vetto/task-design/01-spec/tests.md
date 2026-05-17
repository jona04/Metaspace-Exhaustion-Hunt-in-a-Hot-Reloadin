1. The public runner surfaces (`bin/build`, `bin/integration`, `bin/replay-check`, `bin/run-suite`, `bin/stress`, `src/main/java/io/harbor/textd/cli/HotReloadIntegrationRunner.java`, `src/main/java/io/harbor/textd/cli/HotReloadStressRunner.java`, `src/main/java/io/harbor/textd/cli/RuntimeDigestRunner.java`, and `src/main/java/io/harbor/textd/cli/SessionReplayRunner.java`) remain identical to the shipped task state
2. The 500-cycle reload soak completes successfully with `-XX:MaxMetaspaceSize=64m`
3. The daemon does not throw `java.lang.OutOfMemoryError` during the soak run
4. The baseline processor generation returns the expected deterministic output for the canonical sample record
5. After repeated refreshes, a later sampled revision still returns the expected deterministic output for that same record
6. The auxiliary runtime digest shows the same four worker names at the start and end of the sampled run, and the before/after close checks are true
7. The first replayed session returns the expected outputs, uses the same four worker names throughout, and reports balanced state before and after close
8. The second replayed session returns the expected outputs, uses the same four worker names throughout, and reports balanced state before and after close
9. Class unloading advances after the first replayed session closes
10. Class unloading does not go backwards across the two replayed sessions
11. The replay-check wrapper prints `replay-ok` and positive unloading deltas for both replayed sessions
