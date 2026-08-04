package trs

type HealthStatus struct {
	Status  string `json:"status"`
	Runtime string `json:"runtime"`
	Node    string `json:"node"`
}

type SubmitResult struct {
	Accepted bool     `json:"accepted"`
	RecordID string   `json:"record_id"`
	Errors   []string `json:"errors"`
}

type SyncResult struct {
	AcceptedCount int        `json:"accepted_count"`
	RejectedCount int        `json:"rejected_count"`
	AppendedIDs   []string   `json:"appended_ids"`
	RejectedErrs  [][]string `json:"rejected_errors"`
}
