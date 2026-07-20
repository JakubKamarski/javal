package fixtures.java;

@Deprecated
public class TypeHeaderFormattingSample<T>
        implements NamedType {

    interface NestedType
            extends NamedType {
    }
}

record SplitRecord(
        String value
) implements NamedType {
}

enum SplitState
        implements NamedType {
    ACTIVE
}

@interface SplitMarker
{
}

interface NamedType {
}
