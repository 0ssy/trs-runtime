import XCTest
@testable import TRSSDK

final class TRSSDKTests: XCTestCase {
    func testClientConstruction() {
        _ = TRSClient(baseURL: "http://127.0.0.1:8080")
    }
}

