package demo.tracking;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

class SampleTrackerServiceIT {

    @Autowired
    private SampleTrackerService trackerService;

    @Test
    void synchronizeStatusesPersistsShipmentStatuses() {
        trackerService.synchronizeStatuses();
    }
}
