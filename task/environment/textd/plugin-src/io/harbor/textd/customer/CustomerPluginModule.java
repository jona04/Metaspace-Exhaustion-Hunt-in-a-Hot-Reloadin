package io.harbor.textd.customer;

import io.harbor.textd.api.PluginModule;
import io.harbor.textd.api.TextProcessor;

public final class CustomerPluginModule implements PluginModule {
    @Override
    public TextProcessor processorFor(long generation) {
        return new PipelineProcessor(generation);
    }
}
