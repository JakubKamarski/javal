package fixtures.java;

public class GenericTypeNosonarSample<RecordStatusT> { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
}

interface GenericTypeNosonarInterface<BatchKeyT> { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
}

public record GenericTypeNosonarRecord<ItemRecordT>(String id) { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
}

public class StandardGenericTypeSample<T> {
}

public class MultiLineGenericTypeNosonarSample<RecordStatusT extends BaseEntity> // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
        implements GenericTypeNosonarInterface<BatchKeyT> {
}

class GoodMethodGenericNosonarSample {

    public static <ItemT> long run( // NOSONAR
        java.util.function.LongFunction<java.util.List<ItemT>> pageByCursor
    ) {
        return 0;
    }
}

class BaseEntity {
}
