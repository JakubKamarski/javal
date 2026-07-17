package demo.tracking;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

class PaymentGatewayServiceMockedIT {

    @Autowired
    private PaymentGatewayService paymentGatewayService;

    @Test
    void settlePersistsPayment() {
        paymentGatewayService.settle();
    }
}
