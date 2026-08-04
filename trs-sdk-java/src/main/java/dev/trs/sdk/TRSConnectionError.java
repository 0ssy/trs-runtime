package dev.trs.sdk;

public final class TRSConnectionError extends RuntimeException {
    public TRSConnectionError(String message, Throwable cause) {
        super(message, cause);
    }
}

