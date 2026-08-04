// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "TRSSDK",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [
        .library(name: "TRSSDK", targets: ["TRSSDK"]),
    ],
    targets: [
        .target(name: "TRSSDK"),
        .testTarget(name: "TRSSDKTests", dependencies: ["TRSSDK"]),
    ]
)

