package io.harbor.textd.core;

public record ProcessingResult(long generation, String output, String workerThread) {
}
