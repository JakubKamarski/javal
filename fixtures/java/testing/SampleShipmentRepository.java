package demo.tracking;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.Repository;

public interface SampleShipmentRepository extends Repository<Object, Long> {

    @Query("select s from Object s where s.waybill = :waybill")
    Object findByWaybill(String waybill);
}
