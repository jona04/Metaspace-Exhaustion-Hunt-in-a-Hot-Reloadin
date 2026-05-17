package io.harbor.textd.api;

public interface PluginModule extends AutoCloseable {
    TextProcessor processorFor(long generation);

    @Override
    default void close() {
    }
}
