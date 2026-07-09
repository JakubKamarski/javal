package demo.tracking;

public class CoveredShipmentFacade {

    private final InternalShipmentService internalShipmentService;

    public CoveredShipmentFacade(InternalShipmentService internalShipmentService) {
        this.internalShipmentService = internalShipmentService;
    }

    public void persistShipment(String waybill) {
        internalShipmentService.persist(waybill);
    }
}
