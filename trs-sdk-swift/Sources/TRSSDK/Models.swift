import Foundation

public struct HealthStatus: Codable {
    public let status: String
    public let runtime: String
    public let node: String
}

public struct SubmitResult: Codable {
    public let accepted: Bool
    public let record_id: String
    public let errors: [String]
}

public struct SyncResult: Codable {
    public let accepted_count: Int
    public let rejected_count: Int
    public let appended_ids: [String]
    public let rejected_errors: [[String]]
}

