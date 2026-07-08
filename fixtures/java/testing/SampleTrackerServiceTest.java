package demo.tracking;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class SampleTrackerServiceTest {

    @Mock
    private SampleTrackerGateway gateway;

    @InjectMocks
    private SampleTrackerService trackerService;

    @Test
    void synchronizeStatusesDelegatesToGateway() {
        trackerService.synchronizeStatuses();
    }
}
