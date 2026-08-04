import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public final class TRSClient {
    private let baseURL: URL
    private let session: URLSession
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    public init(baseURL: String, timeoutSeconds: TimeInterval = 5.0) {
        let normalized = baseURL.replacingOccurrences(of: "/+$", with: "", options: .regularExpression)
        self.baseURL = URL(string: normalized)! // caller-provided
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = timeoutSeconds
        self.session = URLSession(configuration: config)
    }

    public func health() async throws -> HealthStatus {
        try await send(path: "/health", method: "GET", body: Optional<[String: String]>.none, decode: HealthStatus.self)
    }

    public func submit(record: [String: Any]) async throws -> SubmitResult {
        let result: SubmitResult = try await send(path: "/submit", method: "POST", body: ["record": record], decode: SubmitResult.self)
        if !result.accepted {
            throw TRSError.validation("record rejected by verifier", result.errors)
        }
        return result
    }

    public func query(expr: [String: Any]) async throws -> [[String: Any]] {
        let payload = try await sendObject(path: "/query", method: "POST", body: ["query": expr])
        guard let records = payload["records"] as? [[String: Any]] else {
            throw TRSError.protocolError("records must be an array")
        }
        return records
    }

    public func sync(records: [[String: Any]]) async throws -> SyncResult {
        try await send(path: "/sync", method: "POST", body: ["records": records], decode: SyncResult.self)
    }

    public func replay() async throws -> [String: Any] {
        try await sendObject(path: "/replay", method: "POST", body: [String: String]())
    }

    private func send<T: Decodable>(path: String, method: String, body: Any?, decode: T.Type) async throws -> T {
        let data = try await sendRaw(path: path, method: method, body: body)
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw TRSError.protocolError("decode failure: \(error.localizedDescription)")
        }
    }

    private func sendObject(path: String, method: String, body: Any?) async throws -> [String: Any] {
        let data = try await sendRaw(path: path, method: method, body: body)
        let json = try JSONSerialization.jsonObject(with: data)
        guard let map = json as? [String: Any] else {
            throw TRSError.protocolError("response must be an object")
        }
        return map
    }

    private func sendRaw(path: String, method: String, body: Any?) async throws -> Data {
        var request = URLRequest(url: baseURL.appendingPathComponent(path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))))
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw TRSError.connection(error.localizedDescription)
        }
        guard let http = response as? HTTPURLResponse else {
            throw TRSError.protocolError("invalid response")
        }

        if !(200...299).contains(http.statusCode) {
            let message = String(data: data, encoding: .utf8) ?? "http \(http.statusCode)"
            if (400...499).contains(http.statusCode) {
                throw TRSError.validation(message, [])
            }
            throw TRSError.server(message)
        }
        return data
    }
}
