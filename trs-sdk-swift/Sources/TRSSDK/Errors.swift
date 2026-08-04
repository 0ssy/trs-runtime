import Foundation

public enum TRSError: Error {
    case connection(String)
    case validation(String, [String])
    case server(String)
    case protocolError(String)
}

