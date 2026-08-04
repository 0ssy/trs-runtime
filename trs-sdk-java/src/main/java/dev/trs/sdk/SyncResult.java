package dev.trs.sdk;

import java.util.List;

public record SyncResult(
        int acceptedCount,
        int rejectedCount,
        List<String> appendedIds,
        List<List<String>> rejectedErrors) {}

