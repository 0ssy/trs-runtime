<?php

namespace TrsSdk;

final class TrsClient
{
    private string $baseUrl;
    private float $timeoutSeconds;

    public function __construct(string $baseUrl, float $timeoutSeconds = 5.0)
    {
        $this->baseUrl = rtrim($baseUrl, "/");
        $this->timeoutSeconds = $timeoutSeconds;
    }

    /** @return array<string,mixed> */
    public function health(): array
    {
        return $this->asObject($this->send("GET", "/health"), "health response");
    }

    /** @param array<string,mixed> $record
     *  @return array<string,mixed>
     */
    public function submit(array $record): array
    {
        $out = $this->asObject($this->send("POST", "/submit", ["record" => $record]), "submit response");
        if (($out["accepted"] ?? false) !== true) {
            $errors = [];
            foreach (($out["errors"] ?? []) as $value) {
                $errors[] = (string) $value;
            }
            throw new TrsValidationError("record rejected by verifier", $errors);
        }
        return $out;
    }

    /** @param array<string,mixed> $expr
     *  @return array<int,array<string,mixed>>
     */
    public function query(array $expr): array
    {
        $out = $this->asObject($this->send("POST", "/query", ["query" => $expr]), "query response");
        if (!isset($out["records"]) || !is_array($out["records"])) {
            throw new TrsProtocolError("records must be an array");
        }
        $rows = [];
        foreach ($out["records"] as $item) {
            $rows[] = $this->asObject($item, "record");
        }
        return $rows;
    }

    /** @param array<int,array<string,mixed>> $records
     *  @return array<string,mixed>
     */
    public function sync(array $records): array
    {
        return $this->asObject($this->send("POST", "/sync", ["records" => $records]), "sync response");
    }

    /** @return array<string,mixed> */
    public function replay(): array
    {
        return $this->asObject($this->send("POST", "/replay", []), "replay response");
    }

    /** @return mixed */
    private function send(string $method, string $path, ?array $body = null)
    {
        $headers = "Accept: application/json\r\n";
        $content = "";
        if ($body !== null) {
            $headers .= "Content-Type: application/json\r\n";
            $content = json_encode($body, JSON_THROW_ON_ERROR);
        }
        $context = stream_context_create([
            "http" => [
                "method" => $method,
                "header" => $headers,
                "content" => $content,
                "timeout" => $this->timeoutSeconds,
                "ignore_errors" => true,
            ]
        ]);

        $url = $this->baseUrl . $path;
        $raw = @file_get_contents($url, false, $context);
        if ($raw === false) {
            throw new TrsConnectionError("connection error");
        }

        $statusLine = $http_response_header[0] ?? "";
        preg_match('/\s(\d{3})\s/', $statusLine, $matches);
        $code = isset($matches[1]) ? (int)$matches[1] : 0;
        $payload = trim($raw) === "" ? [] : json_decode($raw, true);
        if ($payload === null && trim($raw) !== "") {
            throw new TrsProtocolError("invalid JSON response from trs-node");
        }
        if ($code >= 200 && $code < 300) {
            return $payload;
        }
        $message = $this->extractErrorMessage($payload, $code);
        if ($code >= 400 && $code < 500) {
            throw new TrsValidationError($message);
        }
        throw new TrsServerError($message);
    }

    /** @param mixed $value
     *  @return array<string,mixed>
     */
    private function asObject($value, string $label): array
    {
        if (!is_array($value)) {
            throw new TrsProtocolError("$label must be an object");
        }
        return $value;
    }

    /** @param mixed $payload */
    private function extractErrorMessage($payload, int $status): string
    {
        if (is_array($payload)) {
            if (isset($payload["detail"]) && is_string($payload["detail"]) && $payload["detail"] !== "") {
                return $payload["detail"];
            }
            if (isset($payload["error"]) && is_string($payload["error"]) && $payload["error"] !== "") {
                return $payload["error"];
            }
        }
        return "http $status";
    }
}

