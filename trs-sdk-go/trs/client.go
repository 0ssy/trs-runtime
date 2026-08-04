package trs

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type Client struct {
	baseURL    string
	httpClient *http.Client
}

func NewClient(baseURL string, timeout time.Duration) *Client {
	if timeout <= 0 {
		timeout = 5 * time.Second
	}
	return &Client{
		baseURL: strings.TrimRight(baseURL, "/"),
		httpClient: &http.Client{
			Timeout: timeout,
		},
	}
}

func (c *Client) Health(ctx context.Context) (HealthStatus, error) {
	var out HealthStatus
	payload, err := c.send(ctx, http.MethodGet, "/health", nil)
	if err != nil {
		return out, err
	}
	if err := decodeObject(payload, &out, "health response"); err != nil {
		return out, err
	}
	return out, nil
}

func (c *Client) Submit(ctx context.Context, record map[string]any) (SubmitResult, error) {
	var out SubmitResult
	payload, err := c.send(ctx, http.MethodPost, "/submit", map[string]any{"record": record})
	if err != nil {
		return out, err
	}
	if err := decodeObject(payload, &out, "submit response"); err != nil {
		return out, err
	}
	if !out.Accepted {
		return out, &ValidationError{Message: "record rejected by verifier", Errors: out.Errors}
	}
	return out, nil
}

func (c *Client) Query(ctx context.Context, expr map[string]any) ([]map[string]any, error) {
	payload, err := c.send(ctx, http.MethodPost, "/query", map[string]any{"query": expr})
	if err != nil {
		return nil, err
	}
	root, ok := payload.(map[string]any)
	if !ok {
		return nil, &ProtocolError{Message: "query response must be an object"}
	}
	recordsRaw, ok := root["records"].([]any)
	if !ok {
		return nil, &ProtocolError{Message: "records must be an array"}
	}
	records := make([]map[string]any, 0, len(recordsRaw))
	for _, item := range recordsRaw {
		obj, ok := item.(map[string]any)
		if !ok {
			return nil, &ProtocolError{Message: "record must be an object"}
		}
		records = append(records, obj)
	}
	return records, nil
}

func (c *Client) Sync(ctx context.Context, records []map[string]any) (SyncResult, error) {
	var out SyncResult
	payload, err := c.send(ctx, http.MethodPost, "/sync", map[string]any{"records": records})
	if err != nil {
		return out, err
	}
	if err := decodeObject(payload, &out, "sync response"); err != nil {
		return out, err
	}
	return out, nil
}

func (c *Client) Replay(ctx context.Context) (map[string]any, error) {
	payload, err := c.send(ctx, http.MethodPost, "/replay", map[string]any{})
	if err != nil {
		return nil, err
	}
	obj, ok := payload.(map[string]any)
	if !ok {
		return nil, &ProtocolError{Message: "replay response must be an object"}
	}
	return obj, nil
}

func (c *Client) send(ctx context.Context, method string, path string, body any) (any, error) {
	u, err := url.Parse(c.baseURL + path)
	if err != nil {
		return nil, &ConnectionError{Message: err.Error()}
	}

	var reader io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, &ProtocolError{Message: err.Error()}
		}
		reader = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, method, u.String(), reader)
	if err != nil {
		return nil, &ConnectionError{Message: err.Error()}
	}
	req.Header.Set("Accept", "application/json")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, &ConnectionError{Message: err.Error()}
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &ConnectionError{Message: err.Error()}
	}
	var payload any = map[string]any{}
	if len(raw) > 0 {
		if err := json.Unmarshal(raw, &payload); err != nil {
			return nil, &ProtocolError{Message: "invalid JSON response from trs-node"}
		}
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		msg := errorMessageFromPayload(payload, resp.StatusCode)
		if resp.StatusCode >= 400 && resp.StatusCode < 500 {
			return nil, &ValidationError{Message: msg}
		}
		return nil, &ServerError{Message: msg}
	}
	return payload, nil
}

func decodeObject(payload any, target any, label string) error {
	obj, ok := payload.(map[string]any)
	if !ok {
		return &ProtocolError{Message: fmt.Sprintf("%s must be an object", label)}
	}
	b, err := json.Marshal(obj)
	if err != nil {
		return &ProtocolError{Message: err.Error()}
	}
	if err := json.Unmarshal(b, target); err != nil {
		return &ProtocolError{Message: err.Error()}
	}
	return nil
}

func errorMessageFromPayload(payload any, code int) string {
	obj, ok := payload.(map[string]any)
	if !ok {
		return fmt.Sprintf("http %d", code)
	}
	if detail, ok := obj["detail"].(string); ok && detail != "" {
		return detail
	}
	if message, ok := obj["error"].(string); ok && message != "" {
		return message
	}
	return fmt.Sprintf("http %d", code)
}

func IsConnectionError(err error) bool {
	var target *ConnectionError
	return errors.As(err, &target)
}

func IsValidationError(err error) bool {
	var target *ValidationError
	return errors.As(err, &target)
}

func IsServerError(err error) bool {
	var target *ServerError
	return errors.As(err, &target)
}

func IsProtocolError(err error) bool {
	var target *ProtocolError
	return errors.As(err, &target)
}
