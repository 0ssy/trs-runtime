package dev.trs.sdk;

import java.util.List;

public final class TRSValidationError extends RuntimeException {
    private final List<String> errors;

    public TRSValidationError(String message, List<String> errors) {
        super(message);
        this.errors = errors;
    }

    public List<String> errors() {
        return errors;
    }
}

