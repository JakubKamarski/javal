package fixtures.samples;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ConfigurationBeanSample {

    @Bean
    LockProvider lockProvider() {
        return null;
    }

    public void synchronizeStatuses() {
        // non-bean methods still require verb prefix
    }

    private static final class LockProvider {
    }
}
