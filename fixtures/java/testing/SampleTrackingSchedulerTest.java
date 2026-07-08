package demo.tracking;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class SampleTrackingSchedulerTest {

    @Mock
    private SampleTrackerService trackerService;

    @InjectMocks
    private SampleTrackingScheduler trackingScheduler;

    @Test
    void synchronizeStatusesDelegatesToTrackerService() {
        trackingScheduler.synchronizeStatuses();
    }
}
