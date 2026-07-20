from __future__ import annotations

from tests.conftest import findings_for

CHECK_ID = "spring-configuration-proxy-bean-methods"


def _summaries(analyzer, source: str) -> list[str]:
    findings = analyzer.analyze_source("ProxySample.java", source)
    return [finding.summary for finding in findings if finding.check == CHECK_ID]


def test_lite_mode_with_inter_bean_call_is_flagged(analyzer):
    findings = findings_for(analyzer, "ConfigurationProxyBeanMethodsSample.java", CHECK_ID)
    assert len(findings) == 1
    assert "unsafe" in findings[0].summary
    assert "clientFactory()" in findings[0].summary
    # anchored on the offending inter-bean call, not the class annotation
    assert findings[0].line == 11


def test_default_mode_without_inter_bean_calls_recommends_lite_mode(analyzer):
    source = """
package fixtures.samples;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class SafeConfig {
    @Bean
    Reader reader() {
        return new Reader();
    }

    @Bean
    Writer writer() {
        return new Writer();
    }

    static final class Reader {
    }

    static final class Writer {
    }
}
"""
    summaries = _summaries(analyzer, source)
    assert len(summaries) == 1
    assert "safe to set" in summaries[0]
    assert "proxyBeanMethods = false" in summaries[0]


def test_lite_mode_without_inter_bean_calls_is_clean(analyzer):
    source = """
package fixtures.samples;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
class LiteConfig {
    @Bean
    Reader reader() {
        return new Reader();
    }

    static final class Reader {
    }
}
"""
    assert _summaries(analyzer, source) == []


def test_explicit_full_mode_is_deliberate_opt_out(analyzer):
    source = """
package fixtures.samples;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = true)
class FullConfig {
    @Bean
    Reader reader() {
        return new Reader();
    }

    static final class Reader {
    }
}
"""
    assert _summaries(analyzer, source) == []


def test_default_mode_with_inter_bean_call_is_correct_full_mode(analyzer):
    source = """
package fixtures.samples;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class WiringConfig {
    @Bean
    Registry registry() {
        return new Registry(factory());
    }

    @Bean
    Factory factory() {
        return new Factory();
    }

    static final class Registry {
        Registry(Factory factory) {
        }
    }

    static final class Factory {
    }
}
"""
    assert _summaries(analyzer, source) == []


def test_non_configuration_class_is_ignored(analyzer):
    source = """
package fixtures.samples;

import org.springframework.context.annotation.Bean;

class PlainService {
    @Bean
    Reader reader() {
        return new Reader();
    }

    static final class Reader {
    }
}
"""
    assert _summaries(analyzer, source) == []


def test_configuration_without_bean_methods_is_ignored(analyzer):
    source = """
package fixtures.samples;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

@Configuration
@EnableScheduling
class SchedulingConfig {
}
"""
    assert _summaries(analyzer, source) == []


def test_qualified_call_to_other_bean_is_not_inter_bean(analyzer):
    source = """
package fixtures.samples;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
class DelegatingConfig {
    private final Helper helper = new Helper();

    @Bean
    Reader reader() {
        return new Reader(helper.factory());
    }

    @Bean
    Factory factory() {
        return new Factory();
    }

    static final class Helper {
        Factory factory() {
            return new Factory();
        }
    }

    static final class Reader {
        Reader(Factory factory) {
        }
    }

    static final class Factory {
    }
}
"""
    # helper.factory() is a qualified call on another object, not a same-class @Bean call.
    assert _summaries(analyzer, source) == []
