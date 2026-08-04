import { TRSProtocolError, TRSValidationError } from "./errors.js";
import type { HealthStatus, SubmitResult, SyncResult } from "./models.js";
import { HTTPTransport } from "./transport.js";

function asObject(value: unknown, name: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TRSProtocolError(`${name} must be an object`);
  }
  return value as Record<string, unknown>;
}

function asArray(value: unknown, name: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new TRSProtocolError(`${name} must be an array`);
  }
  return value;
}

export class TRSClient {
  private readonly transport: HTTPTransport;

  constructor(baseUrl: string, timeoutMs: number = 5000, transport?: HTTPTransport) {
    this.transport = transport ?? new HTTPTransport(baseUrl, timeoutMs);
  }

  async health(): Promise<HealthStatus> {
    const payload = asObject(await this.transport.get("/health"), "health response");
    return {
      status: String(payload.status ?? ""),
      runtime: String(payload.runtime ?? ""),
      node: String(payload.node ?? ""),
    };
  }

  async submit(record: Record<string, unknown>): Promise<SubmitResult> {
    const payload = asObject(await this.transport.post("/submit", { record }), "submit response");
    const result: SubmitResult = {
      accepted: Boolean(payload.accepted),
      record_id: String(payload.record_id ?? ""),
      errors: asArray(payload.errors ?? [], "errors").map((value) => String(value)),
    };
    if (!result.accepted) {
      throw new TRSValidationError("record rejected by verifier", result.errors);
    }
    return result;
  }

  async query(expr: Record<string, unknown>): Promise<Record<string, unknown>[]> {
    const payload = asObject(await this.transport.post("/query", { query: expr }), "query response");
    return asArray(payload.records ?? [], "records").map((value) => asObject(value, "record"));
  }

  async sync(records: Record<string, unknown>[]): Promise<SyncResult> {
    const payload = asObject(await this.transport.post("/sync", { records }), "sync response");
    const rejectedErrors = asArray(payload.rejected_errors ?? [], "rejected_errors").map((entry) =>
      asArray(entry, "rejected_errors entry").map((value) => String(value)),
    );
    return {
      accepted_count: Number(payload.accepted_count ?? 0),
      rejected_count: Number(payload.rejected_count ?? 0),
      appended_ids: asArray(payload.appended_ids ?? [], "appended_ids").map((value) => String(value)),
      rejected_errors: rejectedErrors,
    };
  }

  async replay(): Promise<Record<string, unknown>> {
    return asObject(await this.transport.post("/replay", {}), "replay response");
  }
}

