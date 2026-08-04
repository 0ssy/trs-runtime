package trs

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func testServer(delay time.Duration) *httptest.Server {
	records := map[string]map[string]any{}
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if delay > 0 {
			time.Sleep(delay)
		}
		writeJSON := func(code int, payload any) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(code)
			_ = json.NewEncoder(w).Encode(payload)
		}

		switch {
		case r.Method == http.MethodGet && r.URL.Path == "/health":
			writeJSON(200, map[string]any{"status": "ok", "runtime": "1.0.0", "node": "0.1.0"})
		case r.Method == http.MethodPost && r.URL.Path == "/submit":
			var body map[string]any
			_ = json.NewDecoder(r.Body).Decode(&body)
			record, _ := body["record"].(map[string]any)
			payload, _ := record["payload"].(map[string]any)
			if _, hasSubject := payload["subject"]; !hasSubject {
				if _, hasGoal := payload["goal"]; !hasGoal {
					if _, hasAction := payload["action"]; !hasAction {
						writeJSON(200, map[string]any{"accepted": false, "record_id": record["id"], "errors": []string{"5.3 Payload Shape"}})
						return
					}
				}
			}
			id, _ := record["id"].(string)
			records[id] = record
			writeJSON(200, map[string]any{"accepted": true, "record_id": id, "errors": []string{}})
		case r.Method == http.MethodPost && r.URL.Path == "/query":
			writeJSON(200, map[string]any{"records": mapsToAnySlice(records)})
		case r.Method == http.MethodPost && r.URL.Path == "/sync":
			var body map[string]any
			_ = json.NewDecoder(r.Body).Decode(&body)
			incoming, _ := body["records"].([]any)
			writeJSON(200, map[string]any{
				"accepted_count":  len(incoming),
				"rejected_count":  0,
				"appended_ids":    []string{"g1"},
				"rejected_errors": [][]string{},
			})
		case r.Method == http.MethodPost && r.URL.Path == "/replay":
			writeJSON(200, map[string]any{"coordination": map[string]any{"unresolved_intentions": []string{}}})
		default:
			writeJSON(404, map[string]any{"error": "not found"})
		}
	}))
}

func mapsToAnySlice(values map[string]map[string]any) []any {
	out := make([]any, 0, len(values))
	for _, value := range values {
		out = append(out, value)
	}
	return out
}

func TestClientFlow(t *testing.T) {
	s := testServer(0)
	defer s.Close()

	client := NewClient(s.URL, 5*time.Second)
	ctx := context.Background()

	health, err := client.Health(ctx)
	if err != nil {
		t.Fatalf("health failed: %v", err)
	}
	if health.Status != "ok" {
		t.Fatalf("unexpected health status: %s", health.Status)
	}

	_, err = client.Submit(ctx, map[string]any{
		"id":      "g1",
		"type":    "Observation",
		"payload": map[string]any{"subject": "boot", "value": 1},
	})
	if err != nil {
		t.Fatalf("submit failed: %v", err)
	}

	records, err := client.Query(ctx, map[string]any{})
	if err != nil {
		t.Fatalf("query failed: %v", err)
	}
	if len(records) != 1 {
		t.Fatalf("expected 1 record, got %d", len(records))
	}

	sync, err := client.Sync(ctx, records)
	if err != nil {
		t.Fatalf("sync failed: %v", err)
	}
	if sync.AcceptedCount != 1 {
		t.Fatalf("unexpected accepted count: %d", sync.AcceptedCount)
	}

	replay, err := client.Replay(ctx)
	if err != nil {
		t.Fatalf("replay failed: %v", err)
	}
	if _, ok := replay["coordination"]; !ok {
		t.Fatalf("missing coordination in replay payload")
	}
}

func TestSubmitValidationError(t *testing.T) {
	s := testServer(0)
	defer s.Close()

	client := NewClient(s.URL, 5*time.Second)
	_, err := client.Submit(context.Background(), map[string]any{
		"id":      "bad",
		"type":    "Observation",
		"payload": map[string]any{},
	})
	if err == nil || !IsValidationError(err) {
		t.Fatalf("expected validation error, got %v", err)
	}
}

func TestTimeoutConnectionError(t *testing.T) {
	s := testServer(200 * time.Millisecond)
	defer s.Close()

	client := NewClient(s.URL, 20*time.Millisecond)
	_, err := client.Health(context.Background())
	if err == nil || !IsConnectionError(err) {
		t.Fatalf("expected connection error, got %v", err)
	}
}
