package fixtures.java;

public class BadGenericTypeNosonarSample<RecordStatusT> {
}

interface BadGenericTypeNosonarInterface<BatchKeyT> {
}

public record BadGenericTypeNosonarRecord<ItemRecordT>(String id) {
}

class BadMixedGenericTypeNosonarSample<T, RecordStatusT> {
}
