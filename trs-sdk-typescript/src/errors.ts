export class TRSError extends Error {}

export class TRSConnectionError extends TRSError {}

export class TRSValidationError extends TRSError {
  readonly errors: string[];

  constructor(message: string, errors: string[] = []) {
    super(message);
    this.errors = errors;
  }
}

export class TRSServerError extends TRSError {}

export class TRSProtocolError extends TRSError {}

