from __future__ import annotations

from tests.conftest import violation_summaries

CHECK_ID = "java-testing-test-method-prefix"
FIXTURE = "BadTestMethodPrefixSampleTest.java"


def test_bad_test_method_prefix_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, FIXTURE, CHECK_ID)
    assert any("shouldFindAllByShipmentIdInWithShipmentFetched" in summary for summary in summaries)
    assert any("findAllByShipmentIdIn" in summary for summary in summaries)


def test_valid_test_method_prefix_is_allowed(analyzer):
    summaries = violation_summaries(analyzer, FIXTURE, CHECK_ID)
    assert all("findAllByShipmentIdIn_WithShipmentFetched" not in summary for summary in summaries)


def test_test_without_when_section_is_ignored(analyzer):
    summaries = violation_summaries(analyzer, FIXTURE, CHECK_ID)
    assert all("checkStatusWithoutSections" not in summary for summary in summaries)


def test_catch_throwable_uses_the_invocation_inside_its_lambda(analyzer):
    source = """
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.catchThrowable;

class UserProviderTest {
    private UserProvider userProvider;

    @Test
    void getByBrandCountry_GivenUnsupportedCountry_WhenCalled_ThenThrows() {
        // GIVEN
        // WHEN
        Throwable thrown = catchThrowable(() -> userProvider.getByBrandCountry("PL"));
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("UserProviderTest.java", source)

    assert not any(finding.check == CHECK_ID for finding in findings)


def test_template_callback_uses_its_single_nested_action(analyzer):
    source = """
import org.junit.jupiter.api.Test;

class PublishingRepositoryIT {
    private CallbackTemplate callbackTemplate;
    private PublishingRepository publishingRepository;

    @Test
    void updatePublished_GivenRows_WhenCommitted_ThenStampsThem() {
        // GIVEN
        // WHEN
        callbackTemplate.executeWithoutResult(status -> publishingRepository.updatePublished());
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("PublishingRepositoryIT.java", source)

    assert not any(finding.check == CHECK_ID for finding in findings)


def test_template_callback_does_not_use_the_wrapper_as_the_tested_method(analyzer):
    source = """
import org.junit.jupiter.api.Test;

class PublishingRepositoryIT {
    private CallbackTemplate callbackTemplate;
    private PublishingRepository publishingRepository;

    @Test
    void executeWithoutResult_GivenRows_WhenCommitted_ThenStampsThem() {
        // GIVEN
        // WHEN
        callbackTemplate.executeWithoutResult(status -> publishingRepository.updatePublished());
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("PublishingRepositoryIT.java", source)
    summaries = [finding.summary for finding in findings if finding.check == CHECK_ID]

    assert len(summaries) == 1
    assert "updatePublished" in summaries[0]


def test_template_callback_with_multiple_actions_is_ignored(analyzer):
    source = """
import org.junit.jupiter.api.Test;

class PublishingRepositoryIT {
    private CallbackTemplate callbackTemplate;
    private PublishingRepository publishingRepository;

    @Test
    void updatePublished_GivenRows_WhenCommitted_ThenStampsThem() {
        // GIVEN
        // WHEN
        callbackTemplate.execute(first -> publishingRepository.updatePublished(),
            second -> publishingRepository.removePublished());
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("PublishingRepositoryIT.java", source)

    assert not any(finding.check == CHECK_ID for finding in findings)
