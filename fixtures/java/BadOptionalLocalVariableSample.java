package fixtures.samples;

import java.util.Optional;

public class BadOptionalLocalVariableSample {

    Optional<String> optionalField;

    public void process() {
        Optional<String> waybill = Optional.empty();
        Optional<String> optionalWaybill = Optional.empty();
    }
}
