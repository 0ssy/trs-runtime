#pragma once

#include <stdexcept>
#include <string>

namespace trs_sdk {

class TrsError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class TrsConnectionError : public TrsError {
public:
    using TrsError::TrsError;
};

class TrsValidationError : public TrsError {
public:
    using TrsError::TrsError;
};

class TrsServerError : public TrsError {
public:
    using TrsError::TrsError;
};

class TrsProtocolError : public TrsError {
public:
    using TrsError::TrsError;
};

class TrsClient {
public:
    explicit TrsClient(std::string base_url);

    std::string health() const;
    std::string submit(const std::string& record_json) const;
    std::string query(const std::string& expr_json) const;
    std::string sync(const std::string& records_json) const;
    std::string replay() const;

private:
    std::string base_url_;
    std::string post_json(const std::string& path, const std::string& body_json) const;
    std::string get_json(const std::string& path) const;
};

}  // namespace trs_sdk

