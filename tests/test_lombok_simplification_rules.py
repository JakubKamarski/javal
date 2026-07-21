from __future__ import annotations


def _findings(analyzer, source: str, check_id: str):
    return [
        finding
        for finding in analyzer.analyze_source("SamplePublishingService.java", source)
        if finding.check == check_id
    ]


def test_lombok_rules_flag_constructor_and_static_factory(analyzer):
    source = """
public final class SamplePublishingService {
    private final SampleStore store;
    private final SamplePublisher publisher;
    private final TimeProvider timeProvider;
    private final SamplePublishingConfig config;
    private final BiConsumer<List<Long>, Exception> failureHandler;

    private SamplePublishingService(
        SampleStore store,
        SamplePublisher publisher,
        TimeProvider timeProvider,
        SamplePublishingConfig config,
        BiConsumer<List<Long>, Exception> failureHandler
    ) {
        this.store = store;
        this.publisher = publisher;
        this.timeProvider = timeProvider;
        this.config = config;
        this.failureHandler = failureHandler;
    }

    public static SamplePublishingService create(
        SampleStore store,
        SamplePublisher publisher,
        TimeProvider timeProvider,
        SamplePublishingConfig config,
        BiConsumer<List<Long>, Exception> failureHandler
    ) {
        return new SamplePublishingService(
            store,
            publisher,
            timeProvider,
            config,
            failureHandler
        );
    }
}
"""

    constructor_findings = _findings(analyzer, source, "java-lombok-required-args-constructor")
    factory_findings = _findings(analyzer, source, "java-lombok-static-factory")

    assert len(constructor_findings) == 1
    assert constructor_findings[0].line == 9
    assert len(factory_findings) == 1
    assert factory_findings[0].line == 23
    assert 'staticName = "create"' in factory_findings[0].suggestion


def test_lombok_constructor_rule_skips_constructor_with_logic(analyzer):
    source = """
class SampleService {
    private final SampleStore store;

    SampleService(SampleStore store) {
        this.store = requireNonNull(store);
    }
}
"""

    assert _findings(analyzer, source, "java-lombok-required-args-constructor") == []


def test_lombok_constructor_rule_allows_class_level_framework_annotations(analyzer):
    source = """
@Component
class SampleService {
    private final SampleStore store;

    SampleService(SampleStore store) {
        this.store = store;
    }
}
"""

    assert len(_findings(analyzer, source, "java-lombok-required-args-constructor")) == 1


def test_lombok_static_factory_rule_skips_transformed_arguments(analyzer):
    source = """
class SampleService {
    private final String code;

    SampleService(String code) {
        this.code = code;
    }

    static SampleService create(String code) {
        return new SampleService(code.trim());
    }
}
"""

    assert len(_findings(analyzer, source, "java-lombok-required-args-constructor")) == 1
    assert _findings(analyzer, source, "java-lombok-static-factory") == []


def test_lombok_rules_skip_annotated_constructor_and_factory(analyzer):
    source = """
class SampleService {
    private final SampleStore store;

    @Inject
    SampleService(SampleStore store) {
        this.store = store;
    }

    static SampleService create(SampleStore store) {
        return new SampleService(store);
    }
}
"""

    assert _findings(analyzer, source, "java-lombok-required-args-constructor") == []
    assert _findings(analyzer, source, "java-lombok-static-factory") == []
