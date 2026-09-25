#!/usr/bin/env bash
set -u

CLUSTER="homelab"
NAMESPACE="tripforge"
MAX_WAIT=120

ok()   { printf '[OK] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

printf '\n=== TripForge Local Environment Startup ===\n\n'

# 1. Docker
if ! docker info >/dev/null 2>&1; then
    fail "Docker is not available. Start Docker Desktop and run this script again."
fi
ok "Docker is running"

# 2. k3d cluster
CLUSTER_STATE="$(k3d cluster list 2>/dev/null | awk -v c="$CLUSTER" '$1 == c {print $2; exit}')"

if [[ -z "$CLUSTER_STATE" ]]; then
    fail "k3d cluster '$CLUSTER' does not exist. This script will not create or delete clusters."
fi

if [[ "$CLUSTER_STATE" != "1/1" ]]; then
    warn "k3d cluster '$CLUSTER' is not fully running. Starting the existing cluster..."
    k3d cluster start "$CLUSTER" >/dev/null || fail "Unable to start k3d cluster '$CLUSTER'."
fi
ok "k3d cluster '$CLUSTER' is running"

# 3. Kubernetes API
printf '[INFO] Waiting for Kubernetes API...\n'

for ((i=1; i<=MAX_WAIT; i++)); do
    if kubectl get --raw=/readyz >/dev/null 2>&1; then
        ok "Kubernetes API is ready"
        break
    fi

    if (( i == MAX_WAIT )); then
        fail "Kubernetes API did not become ready within ${MAX_WAIT}s."
    fi

    sleep 1
done

# 4. Kubernetes nodes
if ! kubectl get nodes --no-headers 2>/dev/null | awk '{print $2}' | grep -q '^Ready$'; then
    kubectl get nodes >&2
    fail "No Kubernetes node is Ready."
fi

NOT_READY="$(kubectl get nodes --no-headers 2>/dev/null | awk '$2 != "Ready" {print $1}')"

if [[ -n "$NOT_READY" ]]; then
    kubectl get nodes >&2
    fail "One or more Kubernetes nodes are not Ready: $NOT_READY"
fi

ok "All Kubernetes nodes are Ready"

# 5. Kubernetes DNS
if ! kubectl run tripforge-dns-check --rm -i --restart=Never \
    --image=busybox:1.36 --quiet -- \
    nslookup kubernetes.default.svc.cluster.local >/dev/null 2>&1; then
    fail "Kubernetes DNS check failed."
fi

ok "Kubernetes DNS is working"

# 6. TripForge namespace
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    fail "Namespace '$NAMESPACE' does not exist."
fi

# 7. TripForge workloads
if ! kubectl wait --for=condition=ready pod --all \
    -n "$NAMESPACE" --timeout=60s >/dev/null 2>&1; then

    kubectl get pods -n "$NAMESPACE" >&2
    fail "One or more TripForge pods are not Ready."
fi

ok "TripForge pods are Ready"

printf '\n=== TripForge Status ===\n'
kubectl get pods -n "$NAMESPACE"

printf '\n'
kubectl get svc -n "$NAMESPACE"

printf '\nTripForge local environment is ready.\n\n'
