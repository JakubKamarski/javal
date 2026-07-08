package demo.tracking;

public class SampleTrackingScheduler {

    private final SampleTrackerService trackerService;

    public SampleTrackingScheduler(SampleTrackerService trackerService) {
        this.trackerService = trackerService;
    }

    public void synchronizeStatuses() {
        trackerService.synchronizeStatuses();
    }
}
