package fixtures.samples;

import org.junit.jupiter.api.Test;

record TrackingConfiguration(int requestBatchSize) {

    int requestBatchSize() {
        return requestBatchSize;
    }

    int computeDbBatchSize(int maxConcurrentRequests) {
        return maxConcurrentRequests * requestBatchSize;
    }
}

class VerbPrefixExemptionsSample {

    void checkStatus() {
    }

    void request() {
    }

    @Override
    public String checkCurrentStatuses() {
        return null;
    }

    @Test
    void checkStatusShouldReturnMappedStatus() {
    }

    void setUp() {
    }
}

class VerbPrefixViolationsSample {

    private Object statusCall() {
        return null;
    }

    private static Object shipment() {
        return null;
    }

    private Object toStatusUpdate() {
        return null;
    }
}
