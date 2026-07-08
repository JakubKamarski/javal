package fixtures.samples;

import java.util.List;
import java.util.stream.Stream;

public class VarLocalVariableSample {

    void localDeclaration() {
        var shipments = List.of("item-1");
        String waybill = "item-2";
    }

    void tryWithResources() throws Exception {
        try (var stream = openStream()) {
            stream.readAllBytes();
        }
    }

    void enhancedFor(List<String> waybills) {
        for (var waybill : waybills) {
            System.out.println(waybill);
        }
    }

    private Stream<java.io.InputStream> openStream() {
        return Stream.empty();
    }
}
