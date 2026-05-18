1. The public runner surfaces (`bin/build`, `bin/integration`, `bin/replay-check`, `bin/run-suite`, `bin/stress`, `src/main/java/io/harbor/textd/cli/HotReloadIntegrationRunner.java`, `src/main/java/io/harbor/textd/cli/HotReloadStressRunner.java`, `src/main/java/io/harbor/textd/cli/RuntimeDigestRunner.java`, and `src/main/java/io/harbor/textd/cli/SessionReplayRunner.java`) remain identical to the shipped task state
2. The project-local JVM profile no longer contains `-XX:+DisableExplicitGC`
3. The daemon core does not add explicit garbage-collection triggers such as `System.gc`, HotSpot diagnostic GC commands, or management-bean GC calls
4. The 500-cycle reload soak completes successfully with `-XX:MaxMetaspaceSize=64m`
5. The daemon does not throw `java.lang.OutOfMemoryError` during the soak run
6. The baseline processor generation returns the expected deterministic output for the canonical sample record
7. After repeated refreshes, a later sampled revision still returns the expected deterministic output for that same record
8. The auxiliary runtime digest shows the same four worker names at the start and end of the sampled run, and the before/after close checks are true
9. The first replayed session returns the expected outputs, uses the same four worker names throughout, and reports balanced state before and after close
10. The second replayed session returns the expected outputs, uses the same four worker names throughout, and reports balanced state before and after close
11. Class unloading advances after the first replayed session closes
12. Class unloading does not go backwards across the two replayed sessions
13. The replay-check wrapper prints `replay-ok` and positive unloading deltas for both replayed sessions
