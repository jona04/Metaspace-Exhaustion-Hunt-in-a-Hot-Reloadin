#!/bin/bash
set -euo pipefail

ROOT_DIR=/workspace/textd

python3 - <<'PY'
from pathlib import Path

thread_cache = Path("/workspace/textd/src/main/java/io/harbor/textd/core/ThreadCache.java")
text_daemon  = Path("/workspace/textd/src/main/java/io/harbor/textd/core/TextDaemon.java")
jvm_cfg      = Path("/opt/textd/jvm.cfg")

# Fix 1: close the old WorkerHandle before replacing it in ThreadCache
tc_text = thread_cache.read_text()
old_handoff = """        if (!cursor.matches(frame)) {\n            cursor = new WorkerHandle(frame);\n            return cursor;\n        }\n"""
new_handoff = """        if (!cursor.matches(frame)) {\n            cursor.close();\n            cursor = new WorkerHandle(frame);\n            return cursor;\n        }\n"""
if old_handoff not in tc_text:
    raise SystemExit("expected thread cache snippet not found")
thread_cache.write_text(tc_text.replace(old_handoff, new_handoff))

# Fix 2: clear each worker thread's ThreadLocal cache on shutdown
daemon_text = text_daemon.read_text()
old_close = """    @Override\n    public void close() throws Exception {\n        revisions.close();\n        workers.shutdownNow();\n        workers.awaitTermination(5, TimeUnit.SECONDS);\n    }\n"""
new_close = """    @Override\n    public void close() throws Exception {\n        drainWorkerCaches();\n        revisions.close();\n        workers.shutdownNow();\n        workers.awaitTermination(5, TimeUnit.SECONDS);\n    }\n\n    private void drainWorkerCaches() throws Exception {\n        CountDownLatch ready = new CountDownLatch(workerCount);\n        CountDownLatch release = new CountDownLatch(1);\n        List<Future<?>> futures = new ArrayList<>();\n        for (int index = 0; index < workerCount; index++) {\n            futures.add(workers.submit(() -> {\n                ready.countDown();\n                if (!release.await(5, TimeUnit.SECONDS)) {\n                    throw new IllegalStateException(\"Worker shutdown release timed out\");\n                }\n                ThreadBridge.clear();\n                return null;\n            }));\n        }\n\n        if (!ready.await(5, TimeUnit.SECONDS)) {\n            throw new IllegalStateException(\"Workers did not become ready for shutdown\");\n        }\n        release.countDown();\n\n        for (Future<?> future : futures) {\n            try {\n                future.get();\n            } catch (ExecutionException exception) {\n                Throwable cause = exception.getCause();\n                if (cause instanceof Exception checked) {\n                    throw checked;\n                }\n                if (cause instanceof Error error) {\n                    throw error;\n                }\n                throw new RuntimeException(cause);\n            }\n        }\n    }\n"""
if old_close not in daemon_text:
    raise SystemExit("expected text daemon close snippet not found")
text_daemon.write_text(daemon_text.replace(old_close, new_close))

# Fix 3: clear the JVM options file so System.gc() works again
jvm_cfg.write_text('')
PY

cd "$ROOT_DIR"
./bin/run-suite >/tmp/textd-oracle-suite.log
