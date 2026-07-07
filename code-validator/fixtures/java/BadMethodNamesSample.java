package fixtures.samples;

import java.util.List;
import java.util.Map;

public class BadMethodNamesSample {

    public Map<String, String> statusByWaybill(List<String> waybills) {
        return Map.of();
    }

    public List<String> distinctShipments(List<String> shipments) {
        return shipments;
    }

    public void synchronizeStatuses() {
        // domain verb not in allowed prefix list
    }

    public boolean empty() {
        return true;
    }
}
