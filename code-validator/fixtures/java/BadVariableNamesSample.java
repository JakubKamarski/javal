package fixtures.samples;

import java.util.List;
import java.util.Map;

public class BadVariableNamesSample {

    private List<String> shipmentList;
    private Map<String, String> statusMap;
    private String strCustomerName;

    public void process(String shipmentList) {
        int intCount = 0;
        List<String> waybillList = List.of();
        Map<String, String> valueByWaybill = Map.of();
    }

    private static final String defaultComparator = "broken";
}
