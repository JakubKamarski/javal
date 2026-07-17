package demo.tracking;

import java.util.function.Function;

public class LibraryOrchestratorService<PayloadT> {

    private final Function<String, PayloadT> payloadMapper;

    public LibraryOrchestratorService(Function<String, PayloadT> payloadMapper) {
        this.payloadMapper = payloadMapper;
    }

    public PayloadT register(String reference) {
        return payloadMapper.apply(reference);
    }
}
