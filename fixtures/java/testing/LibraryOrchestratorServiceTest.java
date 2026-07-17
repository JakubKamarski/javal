package demo.tracking;

import org.junit.jupiter.api.Test;

class LibraryOrchestratorServiceTest {

    @Test
    void registerMapsReferenceThroughFakePort() {
        LibraryOrchestratorService<String> service =
            new LibraryOrchestratorService<>(reference -> reference);

        service.register("REF-1");
    }
}
