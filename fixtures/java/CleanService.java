package fixtures.samples;

import java.util.List;
import java.util.ArrayList;

public class CleanService {

    private final List<String> shipments = new ArrayList<>();

    public List<String> retrieveShipments() {
        return shipments;
    }

    public void updateShipment(String waybill) {
        shipments.add(waybill);
    }

    public boolean isEmpty() {
        return shipments.isEmpty();
    }

    public static CleanService of() {
        return new CleanService();
    }
}
