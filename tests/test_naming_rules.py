from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import FIXTURES_DIR, violation_summaries

BAD_METHODS = FIXTURES_DIR / "BadMethodNamesSample.java"
BAD_VARIABLES = FIXTURES_DIR / "BadVariableNamesSample.java"
CONFIG_BEAN = FIXTURES_DIR / "ConfigurationBeanSample.java"
VERB_EXEMPTIONS = FIXTURES_DIR / "VerbPrefixExemptionsSample.java"
VERB_VIOLATIONS = FIXTURES_DIR / "VerbPrefixExemptionsSample.java"
CLEAN = FIXTURES_DIR / "CleanService.java"


def test_clean_service_has_no_naming_violations(analyzer):
    findings = analyzer.analyze_file(CLEAN)
    naming = [f for f in findings if f.check.startswith("java-naming")]
    assert naming == []


def test_map_style_method_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadMethodNamesSample.java", "java-naming-method-map-style")
    assert any("statusByWaybill" in summary for summary in summaries)


def test_bare_participle_method_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadMethodNamesSample.java", "java-naming-method-bare-participle")
    assert any("distinctShipments" in summary for summary in summaries)
    assert any("empty" in summary for summary in summaries)


def test_prepare_prefix_methods_are_allowed(analyzer):
    source = """
package fixtures.samples;

class PreparePrefixSample {
    private void prepareLoginStub(String login) {
    }

    private void prepareTrackingStub(String waybill) {
    }
}
"""
    findings = analyzer.analyze_source("PreparePrefixSample.java", source)
    verb_prefix = [finding for finding in findings if finding.check == "java-naming-method-verb-prefix"]
    assert verb_prefix == []


def test_reset_prefix_methods_are_allowed(analyzer):
    source = """
package fixtures.samples;

class ResetPrefixSample {
    void resetState() {
    }
}
"""
    findings = analyzer.analyze_source("ResetPrefixSample.java", source)
    verb_prefix = [finding for finding in findings if finding.check == "java-naming-method-verb-prefix"]
    assert verb_prefix == []


def test_count_prefix_methods_are_allowed(analyzer):
    source = """
package fixtures.samples;

class CountPrefixSample {
    int countShipmentsByStatus(String status) {
        return 0;
    }
}
"""
    findings = analyzer.analyze_source("CountPrefixSample.java", source)
    verb_prefix = [finding for finding in findings if finding.check == "java-naming-method-verb-prefix"]
    assert verb_prefix == []


def test_stub_prefix_methods_are_allowed(analyzer):
    source = """
package fixtures.samples;

class StubPrefixSample {
    private void stubResponse(String key) {
    }
}
"""
    findings = analyzer.analyze_source("StubPrefixSample.java", source)
    verb_prefix = [finding for finding in findings if finding.check == "java-naming-method-verb-prefix"]
    assert verb_prefix == []


def test_assert_attach_and_order_prefix_methods_are_allowed(analyzer):
    source = """
package fixtures.samples;

class ActionVerbPrefixSample {
    void assertStored() {
    }

    void attachStatus() {
    }

    void orderWithLabel() {
    }
}
"""
    findings = analyzer.analyze_source("ActionVerbPrefixSample.java", source)
    verb_prefix = [finding for finding in findings if finding.check == "java-naming-method-verb-prefix"]
    assert verb_prefix == []


def test_domain_verbs_are_allowed(analyzer):
    summaries = violation_summaries(analyzer, "BadMethodNamesSample.java", "java-naming-method-verb-prefix")
    assert not any("synchronizeStatuses" in summary for summary in summaries)


def test_noun_only_methods_are_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadMethodNamesSample.java", "java-naming-method-verb-prefix")
    assert any("shipment" in summary for summary in summaries)


def test_configuration_bean_method_does_not_require_verb_prefix(analyzer):
    findings = analyzer.analyze_file(CONFIG_BEAN)
    verb_prefix_findings = [
        f for f in findings if f.check == "java-naming-method-verb-prefix" and "lockProvider" in f.summary
    ]
    assert verb_prefix_findings == []


def test_bean_method_without_configuration_annotation_does_not_require_verb_prefix(analyzer):
    source = """
import org.springframework.context.annotation.Bean;

class FeignClientConfiguration {
    @Bean
    Object addressValidationErrorDecoder() {
        return new Object();
    }
}
"""

    findings = analyzer.analyze_source("FeignClientConfiguration.java", source)

    assert not any("addressValidationErrorDecoder" in finding.summary for finding in findings)


def test_static_factory_returning_enclosing_type_does_not_require_verb_prefix(analyzer):
    source = """
class ServicesErrorMessage {
    static ServicesErrorMessage withConstraintViolations() {
        return new ServicesErrorMessage();
    }

    static Object withUtility() {
        return new Object();
    }
}
"""

    findings = analyzer.analyze_source("ServicesErrorMessage.java", source)
    verb_prefix = [finding.summary for finding in findings if finding.check == "java-naming-method-verb-prefix"]

    assert not any("withConstraintViolations" in summary for summary in verb_prefix)
    assert any("withUtility" in summary for summary in verb_prefix)


def test_method_source_provider_does_not_require_verb_prefix(analyzer):
    source = """
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import java.util.stream.Stream;

class MapperTest {
    @ParameterizedTest
    @MethodSource("errorCodeAndExpectedProperty")
    void map(String value) {
    }

    static Stream<String> errorCodeAndExpectedProperty() {
        return Stream.empty();
    }

    static Stream<String> unsupportedProvider() {
        return Stream.empty();
    }
}
"""

    findings = analyzer.analyze_source("MapperTest.java", source)
    verb_prefix = [finding.summary for finding in findings if finding.check == "java-naming-method-verb-prefix"]

    assert not any("errorCodeAndExpectedProperty" in summary for summary in verb_prefix)
    assert any("unsupportedProvider" in summary for summary in verb_prefix)


def test_decode_prefix_is_allowed(analyzer):
    source = "class Decoder { void decodeResponse() {} }"

    findings = analyzer.analyze_source("Decoder.java", source)

    assert not any(finding.check == "java-naming-method-verb-prefix" for finding in findings)


def test_standard_action_verbs_are_allowed(analyzer):
    source = """
class ActionVerbSample {
    void register() {}
    void registerShipment() {}
    void flush() {}
    void flushAndClear() {}
    void insertIgnoringWaybillConflict() {}
    void setInitialStatus() {}
    void clearCache() {}
}
"""

    findings = analyzer.analyze_source("ActionVerbSample.java", source)
    verb_prefix = [finding for finding in findings if finding.check == "java-naming-method-verb-prefix"]

    assert verb_prefix == []


def test_ship_prefix_is_allowed_without_allowing_shipment_nouns(analyzer):
    source = "class Shipper { void ship() {} void shipShipment() {} void shipment() {} }"

    findings = analyzer.analyze_source("Shipper.java", source)
    verb_prefix = [finding.summary for finding in findings if finding.check == "java-naming-method-verb-prefix"]

    assert not any("ship'" in summary or "shipShipment" in summary for summary in verb_prefix)
    assert any("shipment" in summary for summary in verb_prefix)


def test_non_bean_method_in_configuration_class_still_requires_verb_prefix(analyzer):
    summaries = violation_summaries(analyzer, "ConfigurationBeanSample.java", "java-naming-method-verb-prefix")
    assert not any("synchronizeStatuses" in summary for summary in summaries)


def test_framework_exemptions_skip_verb_prefix_check(analyzer):
    findings = analyzer.analyze_file(VERB_EXEMPTIONS)
    verb_prefix_findings = [f for f in findings if f.check == "java-naming-method-verb-prefix"]
    allowed_fragments = {
        "checkStatus",
        "request",
        "checkCurrentStatuses",
        "checkStatusShouldReturnMappedStatus",
        "setUp",
        "requestBatchSize",
        "computeDbBatchSize",
    }
    assert not any(any(fragment in finding.summary for fragment in allowed_fragments) for finding in verb_prefix_findings)


def test_noun_and_to_prefix_methods_remain_flagged(analyzer):
    findings = analyzer.analyze_file(VERB_VIOLATIONS)
    verb_prefix_findings = [f.summary for f in findings if f.check == "java-naming-method-verb-prefix"]
    assert any("statusCall" in summary for summary in verb_prefix_findings)
    assert any("shipment" in summary for summary in verb_prefix_findings)
    assert any("toStatusUpdate" in summary for summary in verb_prefix_findings)


@pytest.mark.parametrize(
    ("fixture_name", "expected_fragment"),
    [
        ("BadVariableNamesSample.java", "shipmentList"),
        ("BadVariableNamesSample.java", "statusMap"),
        ("BadVariableNamesSample.java", "waybillList"),
    ],
)
def test_collection_type_in_variable_name(analyzer, fixture_name, expected_fragment):
    summaries = violation_summaries(analyzer, fixture_name, "java-naming-variable-collection-type")
    assert any(expected_fragment in summary for summary in summaries)


def test_hungarian_notation_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadVariableNamesSample.java", "java-naming-variable-hungarian")
    assert any("strCustomerName" in summary for summary in summaries)
    assert any("intCount" in summary for summary in summaries)


def test_constant_upper_snake_case_is_enforced(analyzer):
    summaries = violation_summaries(analyzer, "BadVariableNamesSample.java", "java-naming-constant-upper-snake")
    assert any("defaultComparator" in summary for summary in summaries)


def test_serial_version_uid_is_exempt_from_constant_upper_snake_case(analyzer):
    findings = analyzer.analyze_file(FIXTURES_DIR / "SerializableEntitySample.java")
    constant_findings = [
        finding for finding in findings if finding.check == "java-naming-constant-upper-snake"
    ]
    assert constant_findings == []


def test_non_static_final_field_with_static_in_name_is_not_constant(analyzer):
    source = "class Sample {\n    private final String staticName = \"value\";\n}\n"

    findings = analyzer.analyze_source("Sample.java", source)

    assert not any(
        finding.check == "java-naming-constant-upper-snake"
        for finding in findings
    )


def test_value_by_key_variable_is_allowed(analyzer):
    findings = analyzer.analyze_file(BAD_VARIABLES)
    collection_findings = [
        f for f in findings if f.check == "java-naming-variable-collection-type" and "valueByWaybill" in f.summary
    ]
    assert collection_findings == []


def test_domain_mapping_word_does_not_embed_collection_type(analyzer):
    findings = analyzer.analyze_file(BAD_VARIABLES)
    collection_findings = [
        f
        for f in findings
        if f.check == "java-naming-variable-collection-type" and "shipmentStatusMappingByRawStatus" in f.summary
    ]
    assert collection_findings == []
