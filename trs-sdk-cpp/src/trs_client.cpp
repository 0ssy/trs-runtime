#include "trs_sdk/trs_client.hpp"

#include <utility>

namespace trs_sdk {

TrsClient::TrsClient(std::string base_url) : base_url_(std::move(base_url)) {
    while (!base_url_.empty() && base_url_.back() == '/') {
        base_url_.pop_back();
    }
}

std::string TrsClient::health() const {
    return get_json("/health");
}

std::string TrsClient::submit(const std::string& record_json) const {
    return post_json("/submit", "{\"record\":" + record_json + "}");
}

std::string TrsClient::query(const std::string& expr_json) const {
    return post_json("/query", "{\"query\":" + expr_json + "}");
}

std::string TrsClient::sync(const std::string& records_json) const {
    return post_json("/sync", "{\"records\":" + records_json + "}");
}

std::string TrsClient::replay() const {
    return post_json("/replay", "{}");
}

std::string TrsClient::post_json(const std::string& path, const std::string& body_json) const {
    (void)path;
    (void)body_json;
    throw TrsProtocolError("HTTP transport not yet linked. Integrate WinHTTP/cpr/libcurl in next pass.");
}

std::string TrsClient::get_json(const std::string& path) const {
    (void)path;
    throw TrsProtocolError("HTTP transport not yet linked. Integrate WinHTTP/cpr/libcurl in next pass.");
}

}  // namespace trs_sdk

