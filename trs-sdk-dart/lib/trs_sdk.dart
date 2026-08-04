import "dart:convert";
import "dart:io";

class TrsConnectionError implements Exception {
  final String message;
  TrsConnectionError(this.message);
  @override
  String toString() => message;
}

class TrsValidationError implements Exception {
  final String message;
  final List<String> errors;
  TrsValidationError(this.message, [this.errors = const []]);
  @override
  String toString() => message;
}

class TrsServerError implements Exception {
  final String message;
  TrsServerError(this.message);
  @override
  String toString() => message;
}

class TrsProtocolError implements Exception {
  final String message;
  TrsProtocolError(this.message);
  @override
  String toString() => message;
}

class TrsClient {
  final String _baseUrl;
  final Duration _timeout;
  final HttpClient _http = HttpClient();

  TrsClient(String baseUrl, {Duration timeout = const Duration(seconds: 5)})
      : _baseUrl = baseUrl.replaceAll(RegExp(r"/+$"), ""),
        _timeout = timeout;

  Future<Map<String, dynamic>> health() async {
    final payload = await _send("GET", "/health");
    return _asMap(payload, "health response");
  }

  Future<Map<String, dynamic>> submit(Map<String, dynamic> record) async {
    final payload = await _send("POST", "/submit", {"record": record});
    final out = _asMap(payload, "submit response");
    if (out["accepted"] != true) {
      throw TrsValidationError(
        "record rejected by verifier",
        (out["errors"] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
      );
    }
    return out;
  }

  Future<List<Map<String, dynamic>>> query(Map<String, dynamic> expr) async {
    final payload = await _send("POST", "/query", {"query": expr});
    final map = _asMap(payload, "query response");
    final rows = map["records"];
    if (rows is! List) {
      throw TrsProtocolError("records must be an array");
    }
    return rows.map((e) => _asMap(e, "record")).toList();
  }

  Future<Map<String, dynamic>> sync(List<Map<String, dynamic>> records) async {
    final payload = await _send("POST", "/sync", {"records": records});
    return _asMap(payload, "sync response");
  }

  Future<Map<String, dynamic>> replay() async {
    final payload = await _send("POST", "/replay", <String, dynamic>{});
    return _asMap(payload, "replay response");
  }

  Future<dynamic> _send(String method, String path, [Object? body]) async {
    final uri = Uri.parse("$_baseUrl$path");
    HttpClientRequest request;
    try {
      request = await _http.openUrl(method, uri).timeout(_timeout);
    } catch (e) {
      throw TrsConnectionError(e.toString());
    }
    request.headers.set(HttpHeaders.acceptHeader, "application/json");
    if (body != null) {
      request.headers.set(HttpHeaders.contentTypeHeader, "application/json");
      request.write(jsonEncode(body));
    }

    HttpClientResponse response;
    try {
      response = await request.close().timeout(_timeout);
    } catch (e) {
      throw TrsConnectionError(e.toString());
    }

    final raw = await response.transform(utf8.decoder).join();
    final payload = raw.trim().isEmpty ? <String, dynamic>{} : jsonDecode(raw);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return payload;
    }
    final message = _extractErrorMessage(payload, response.statusCode);
    if (response.statusCode >= 400 && response.statusCode < 500) {
      throw TrsValidationError(message);
    }
    throw TrsServerError(message);
  }

  Map<String, dynamic> _asMap(dynamic value, String label) {
    if (value is Map<String, dynamic>) {
      return value;
    }
    throw TrsProtocolError("$label must be an object");
  }

  String _extractErrorMessage(dynamic payload, int status) {
    if (payload is Map<String, dynamic>) {
      final detail = payload["detail"];
      if (detail is String && detail.isNotEmpty) {
        return detail;
      }
      final error = payload["error"];
      if (error is String && error.isNotEmpty) {
        return error;
      }
    }
    return "http $status";
  }
}

