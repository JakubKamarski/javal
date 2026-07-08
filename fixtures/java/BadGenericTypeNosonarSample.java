package fixtures.java;

public class BadGenericTypeNosonarSample<ShipmentStatusT> {
}

interface BadGenericTypeNosonarInterface<GroupKeyT> {
}

public record BadGenericTypeNosonarRecord<TrackableItemT>(String id) {
}

class BadMixedGenericTypeNosonarSample<T, ShipmentStatusT> {
}
