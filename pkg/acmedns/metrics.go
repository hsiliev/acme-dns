package acmedns

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	ChallengeSuccessCount = promauto.NewCounter(prometheus.CounterOpts{
		Name: "acmedns_challenge_success_total",
		Help: "The total number of successful TXT record queries for ACME challenges",
	})
	ChallengeFailureCount = promauto.NewCounter(prometheus.CounterOpts{
		Name: "acmedns_challenge_failure_total",
		Help: "The total number of failed TXT record queries for ACME challenges",
	})
)
