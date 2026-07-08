package demo.tracking;

import com.lpp.locus.libs.common.tests.spring.slice.SpringBootIT;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

@SpringBootIT
class SampleTrackerServiceIT {

    @Autowired
    private SampleTrackerService trackerService;

    @Test
    void synchronizeStatusesPersistsShipmentStatuses() {
        trackerService.synchronizeStatuses();
    }
}
