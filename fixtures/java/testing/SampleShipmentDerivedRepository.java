package demo.tracking;

import org.springframework.data.repository.Repository;

public interface SampleShipmentDerivedRepository extends Repository<Object, Long> {

    Object findByWaybill(String waybill);
}
