package api

import (
	"net/http"

	"github.com/julienschmidt/httprouter"
)

const (
	healthyResponse   = `{"status":"healthy"}`
	unhealthyResponse = `{"status":"unhealthy"}`
)

// Endpoint used to check the readiness and/or liveness (health) of the server.
func (a *AcmednsAPI) healthCheck(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
	err := a.DB.GetBackend().Ping()
	if err != nil {
		a.Logger.Errorw("Health check failed: database unreachable", "error", err)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_, _ = w.Write([]byte(unhealthyResponse))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write([]byte(healthyResponse))
}
