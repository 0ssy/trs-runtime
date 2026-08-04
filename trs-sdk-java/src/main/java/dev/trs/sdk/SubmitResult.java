package dev.trs.sdk;

import java.util.List;

public record SubmitResult(boolean accepted, String recordId, List<String> errors) {}

