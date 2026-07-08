package fixtures.java;

public class GenericTypeNosonarSample<ShipmentStatusT> { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
}

interface GenericTypeNosonarInterface<GroupKeyT> { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
}

public record GenericTypeNosonarRecord<TrackableItemT>(String id) { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
}

public class StandardGenericTypeSample<T> {
}

public class MultiLineGenericTypeNosonarSample<ShipmentStatusT extends BaseEntity> // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
        implements GenericTypeNosonarInterface<GroupKeyT> {
}

class BaseEntity {
}
