package fixtures.java;

public interface BadGenericMethodNosonarSample<GroupKeyT> { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.

    static <GroupKeyT> BadGenericMethodNosonarSample<GroupKeyT> createNoOp() {
        return null;
    }
}

class BadMethodOnlyGenericNosonarSample {

    public static <ItemT> long run() {
        return 0;
    }
}

class BadDescriptiveMethodNosonarSample {

    public static <ItemT> long run() { // NOSONAR: descriptive business generic name is clearer than a single-letter type parameter.
        return 0;
    }
}

class GoodStandardMethodGenericSample {

    public static <T> T identity(T value) {
        return value;
    }
}
