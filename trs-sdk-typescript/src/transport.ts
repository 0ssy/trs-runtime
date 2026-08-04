import { TRSConnectionError, TRSServerError, TRSValidationError } from "./errors.js";

export class HTTPTransport {
  constructor(private readonly baseUrl: string, private readonly timeoutMs: number = 5000) {}

  async get(path: string): Promise<unknown> {
    return this.send("GET", path);
  }

  async post(path: string, payload: object): Promise<unknown> {
    return this.send("POST", path, payload);
  }

  private async send(method: "GET" | "POST", path: string, payload?: object): Promise<unknown> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl.replace(/\/+$/, "")}${path}`, {
        method,
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: payload ? JSON.stringify(payload) : undefined,
        signal: controller.signal,
      });
      const text = await response.text();
      const parsed = text ? JSON.parse(text) : {};
      if (!response.ok) {
        const detail = typeof parsed?.detail === "string" ? parsed.detail : typeof parsed?.error === "string" ? parsed.error : `http ${response.status}`;
        if (response.status >= 400 && response.status < 500) {
          throw new TRSValidationError(detail);
        }
        throw new TRSServerError(detail);
      }
      return parsed;
    } catch (err) {
      if (err instanceof TRSValidationError || err instanceof TRSServerError) {
        throw err;
      }
      throw new TRSConnectionError(String(err));
    } finally {
      clearTimeout(timer);
    }
  }
}

