package fixtures.samples;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class BadTestWhenVariableSample {

    @Test
    void checkStatus_GivenWaybill_WhenChecked_ThenReturnsStatus() {
        // GIVEN
        String waybill = "WB-1";

        // WHEN
        String result = "DELIVERED";

        // THEN
        assertThat(result).isEqualTo("DELIVERED");
    }

    @Test
    void checkStatusWithoutSections() {
        String result = "DELIVERED";
        assertThat(result).isEqualTo("DELIVERED");
    }

    @Test
    void checkStatus_GivenWaybill_WhenChecked_ThenReturnsMappedStatus() {
        // GIVEN
        String waybill = "WB-1";

        // WHEN
        String shipmentStatus = "DELIVERED";

        // THEN
        assertThat(shipmentStatus).isEqualTo("DELIVERED");
    }
}
