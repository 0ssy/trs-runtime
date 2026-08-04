require "net/http"
require "json"
require_relative "errors"

module TrsSdk
  class Client
    def initialize(base_url, timeout_seconds: 5)
      @base_url = base_url.gsub(%r{/+$}, "")
      @timeout = timeout_seconds
    end

    def health
      as_object(send_request("GET", "/health"), "health response")
    end

    def submit(record)
      out = as_object(send_request("POST", "/submit", { record: record }), "submit response")
      unless out["accepted"] == true
        raise TrsValidationError.new("record rejected by verifier", Array(out["errors"]).map(&:to_s))
      end
      out
    end

    def query(expr)
      out = as_object(send_request("POST", "/query", { query: expr }), "query response")
      rows = out["records"]
      raise TrsProtocolError, "records must be an array" unless rows.is_a?(Array)
      rows.map { |r| as_object(r, "record") }
    end

    def sync(records)
      as_object(send_request("POST", "/sync", { records: records }), "sync response")
    end

    def replay
      as_object(send_request("POST", "/replay", {}), "replay response")
    end

    private

    def send_request(method, path, body = nil)
      uri = URI("#{@base_url}#{path}")
      http = Net::HTTP.new(uri.host, uri.port)
      http.read_timeout = @timeout
      request = method == "POST" ? Net::HTTP::Post.new(uri) : Net::HTTP::Get.new(uri)
      request["Accept"] = "application/json"
      if body
        request["Content-Type"] = "application/json"
        request.body = JSON.generate(body)
      end
      response = http.request(request)
      payload = response.body.to_s.strip.empty? ? {} : JSON.parse(response.body)
      code = response.code.to_i
      return payload if code >= 200 && code < 300
      message = extract_error_message(payload, code)
      raise TrsValidationError.new(message) if code >= 400 && code < 500
      raise TrsServerError, message
    rescue JSON::ParserError
      raise TrsProtocolError, "invalid JSON response from trs-node"
    rescue TrsError
      raise
    rescue StandardError => e
      raise TrsConnectionError, e.message
    end

    def as_object(value, label)
      raise TrsProtocolError, "#{label} must be an object" unless value.is_a?(Hash)
      value
    end

    def extract_error_message(payload, code)
      return payload["detail"] if payload.is_a?(Hash) && payload["detail"].is_a?(String) && !payload["detail"].empty?
      return payload["error"] if payload.is_a?(Hash) && payload["error"].is_a?(String) && !payload["error"].empty?
      "http #{code}"
    end
  end
end

