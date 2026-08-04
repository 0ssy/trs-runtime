package trs

type ConnectionError struct {
	Message string
}

func (e *ConnectionError) Error() string { return e.Message }

type ValidationError struct {
	Message string
	Errors  []string
}

func (e *ValidationError) Error() string { return e.Message }

type ServerError struct {
	Message string
}

func (e *ServerError) Error() string { return e.Message }

type ProtocolError struct {
	Message string
}

func (e *ProtocolError) Error() string { return e.Message }
