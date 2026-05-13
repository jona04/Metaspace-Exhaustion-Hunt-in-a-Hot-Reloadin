package io.harbor.textd.customer;

import io.harbor.textd.api.PluginModule;
import io.harbor.textd.api.PluginModuleFactory;

public final class CustomerPluginFactory implements PluginModuleFactory {
    @Override
    public PluginModule open() {
        return new CustomerPluginModule();
    }
}
