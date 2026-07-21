from __future__ import annotations

CHECK_ID = "java-style-empty-collection-static-factory"


def test_flags_empty_list_map_and_set_static_factories(analyzer):
    source = """
import java.util.List;
import java.util.Map;
import java.util.Set;

class Sample {
    void execute() {
        List.of();
        Map.of();
        Set.of();
        List.<String>of();
    }
}
"""

    findings = analyzer.analyze_source("Sample.java", source)
    summaries = [finding.summary for finding in findings if finding.check == CHECK_ID]

    assert len(summaries) == 4
    assert any("Collections.emptyList()" in summary for summary in summaries)
    assert any("Collections.emptyMap()" in summary for summary in summaries)
    assert any("Collections.emptySet()" in summary for summary in summaries)


def test_allows_non_empty_static_factories_and_collections_empty_factories(analyzer):
    source = """
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;

class Sample {
    void execute() {
        List.of("value");
        Map.of("key", "value");
        Set.of("value");
        Collections.emptyList();
        Collections.emptyMap();
        Collections.emptySet();
    }
}
"""

    findings = analyzer.analyze_source("Sample.java", source)

    assert not any(finding.check == CHECK_ID for finding in findings)
