package io.harbor.textd.core;

final class ThreadBridge {
    private static final ThreadLocal<ThreadCache> ROUTES = ThreadLocal.withInitial(ThreadCache::new);

    private ThreadBridge() {
    }

    static WorkerHandle current(TimelineLedger ledger) {
        return ROUTES.get().cursorFor(ledger);
    }
}
