package demo;

/** Public API for sample processing. */
public class GoodCommentSample {

    /** Returns the current count. */
    public int getCount() {
        return 0; // NOSONAR: intentional stub
    }

    // PLOG-1234 TODO: replace stub implementation
    void plannedWork() {
    }

    /**
     * @deprecated Remove in 2027-Q1; use {@link #getCount()} instead.
     */
    @Deprecated
    public int legacyCount() {
        return 0;
    }

    void gwtStyleTest() {
        // GIVEN
        int value = 1;
        // WHEN
        int doubled = value + value;
        // THEN
        int ignored = doubled;
    }
}
