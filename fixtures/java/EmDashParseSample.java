package fixtures.samples;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.util.List;

class EmDashParseSample {

    @AfterEach
    void resetState() {
        List.<String>of();
    }

    @Test
    void executeFirstScenarioWithLongMethodNameThatSpansParserBoundaryOne() {
        stubResponse("item-a", """
            {"id":"1"}
            """);
        // WHEN — em dash in a comment can desync tree-sitter-java
        checkValues(List.of("item-a"));
    }

    @Test
    void executeSecondScenarioWithEquallyLongMethodNameThatMustStayIntactTwo() {
        checkValues(List.of("item-b"));
    }

    private void stubResponse(String key, String body) {
        checkValues(List.of(key, body));
    }

    private void checkValues(List<String> values) {
        values.forEach(value -> List.of(value));
    }
}
