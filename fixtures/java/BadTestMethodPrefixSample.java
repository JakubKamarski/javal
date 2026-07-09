package fixtures.samples;

import java.util.List;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class BadTestMethodPrefixSample {

    @Test
    void shouldFindAllByShipmentIdInWithShipmentFetched() {
        // GIVEN
        SampleRepository repository = new SampleRepository();

        // WHEN
        List<String> shipmentStatuses = repository.findAllByShipmentIdIn(List.of(1L, 2L));

        // THEN
        assertThat(shipmentStatuses).isNotEmpty();
    }

    @Test
    void findAllByShipmentIdIn_WithShipmentFetched() {
        // GIVEN
        SampleRepository repository = new SampleRepository();

        // WHEN
        List<String> shipmentStatuses = repository.findAllByShipmentIdIn(List.of(1L));

        // THEN
        assertThat(shipmentStatuses).hasSize(1);
    }

    @Test
    void checkStatusWithoutSections() {
        SampleRepository repository = new SampleRepository();
        List<String> shipmentStatuses = repository.findAllByShipmentIdIn(List.of(1L));
        assertThat(shipmentStatuses).isNotEmpty();
    }

    static class SampleRepository {
        List<String> findAllByShipmentIdIn(List<Long> shipmentIds) {
            return List.of("SENT");
        }
    }
}
