package fixtures.samples;

import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.HashSet;

public class UnusedImportsSample {

    private final List<String> shipments = new ArrayList<>();

    public List<String> retrieveShipments() {
        return shipments;
    }
}
