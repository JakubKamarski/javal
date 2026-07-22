from __future__ import annotations

CHECK_ID = "java-style-apache-commons-validate"


def _findings(analyzer, source: str):
    return [
        finding
        for finding in analyzer.analyze_source("SampleService.java", source)
        if finding.check == CHECK_ID
    ]


def test_flags_direct_illegal_argument_exception_guards_for_any_condition(analyzer):
    source = """
class SampleService {
    void configure(int batchSize, String reference, boolean enabled) {
        if (batchSize <= 0) {
            throw new IllegalArgumentException("batchSize must be positive: " + batchSize);
        }
        if (reference == null)
            throw new IllegalArgumentException("reference is required");
        if (!enabled) {
            throw new java.lang.IllegalArgumentException("enabled is required");
        }
    }
}
"""

    findings = _findings(analyzer, source)

    assert [finding.line for finding in findings] == [4, 7, 9]
    assert all("Apache Commons Lang Validate" in finding.summary for finding in findings)
    assert any("Validate.notNull" in finding.suggestion for finding in findings)
    assert any("Validate.isTrue" in finding.suggestion for finding in findings)


def test_allows_validate_and_non_direct_exception_control_flow(analyzer):
    source = """
import org.apache.commons.lang3.Validate;

class SampleService {
    void configure(int batchSize, String reference) {
        Validate.isTrue(batchSize > 0, "batchSize must be positive: %s", batchSize);
        Validate.notNull(reference, "reference is required");
        if (batchSize <= 0) {
            logInvalidBatchSize();
            throw new IllegalArgumentException("batchSize must be positive");
        }
        if (reference == null) {
            throw new NullPointerException("reference is required");
        }
        if (batchSize <= 0) {
            throw new IllegalArgumentException("batchSize must be positive");
        } else {
            processBatch();
        }
    }

    void logInvalidBatchSize() {}
    void processBatch() {}
}
"""

    assert _findings(analyzer, source) == []
