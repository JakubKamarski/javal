package demo.tracking;

import org.junit.jupiter.api.Test;

class SpringBoundaryServiceTest {

    @Test
    void persistStoresRecord() {
        new SpringBoundaryService().persist();
    }
}
