package io.harbor.textd.core;

import java.util.Arrays;
import java.util.Locale;
import java.util.stream.Collectors;

public final class OutputFormat {
    private static final int PIPELINE_WEIGHT = 18528;

    private OutputFormat() {
    }

    public static String expectedFor(long generation, String record) {
        String normalized = Arrays.stream(record.trim().split("\\s+"))
            .filter(token -> !token.isBlank())
            .map(token -> token.toUpperCase(Locale.ROOT))
            .collect(Collectors.joining(">"));
        return String.format(Locale.ROOT, "GEN-%03d|%s|PIPE-%d", generation, normalized, PIPELINE_WEIGHT);
    }
}
