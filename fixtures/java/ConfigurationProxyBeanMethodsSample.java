package fixtures.samples;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class ConfigurationProxyBeanMethodsSample {

    @Bean
    ServiceRegistry serviceRegistry() {
        return new ServiceRegistry(clientFactory());
    }

    @Bean
    ClientFactory clientFactory() {
        return new ClientFactory();
    }

    private static final class ServiceRegistry {
        ServiceRegistry(ClientFactory clientFactory) {
        }
    }

    private static final class ClientFactory {
    }
}
