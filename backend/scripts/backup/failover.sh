#!/bin/bash
set -euo pipefail

# IABANK Disaster Recovery Failover Script
# T086 DR Pilot Light Implementation
# Usage: ./failover.sh [--force] [--dry-run]

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/iabank_failover_$(date +%Y%m%d_%H%M%S).log"
START_TIME=$(date +%s)
DRY_RUN=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--force]"
      echo "  --dry-run   Simulate failover without making changes"
      echo "  --force     Skip confirmation prompts"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Logging function
log() {
  local level=$1
  shift
  local message="$*"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
  log "ERROR" "$1"
  echo "❌ Failover FAILED. Check log: $LOG_FILE"
  exit 1
}

# Prerequisites check
check_prerequisites() {
  log "INFO" "Checking prerequisites..."

  # Check AWS CLI
  if ! command -v aws &> /dev/null; then
    error_exit "AWS CLI not found. Please install AWS CLI."
  fi

  # Check AWS credentials
  if ! aws sts get-caller-identity &> /dev/null; then
    error_exit "AWS credentials not configured or invalid."
  fi

  # Check Terraform (if not dry-run)
  if ! $DRY_RUN && ! command -v terraform &> /dev/null; then
    error_exit "Terraform not found. Please install Terraform."
  fi

  # Check curl
  if ! command -v curl &> /dev/null; then
    error_exit "curl not found. Please install curl."
  fi

  log "INFO" "Prerequisites check passed ✅"
}

# Validate primary status
validate_primary_status() {
  log "INFO" "Validating primary environment status..."

  local primary_status
  if primary_status=$(aws rds describe-db-instances \
    --db-instance-identifier iabank-primary \
    --region us-east-1 \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null); then

    log "INFO" "Primary database status: $primary_status"

    if [[ "$primary_status" == "available" ]] && ! $FORCE; then
      log "WARN" "Primary database appears to be healthy. Use --force to proceed anyway."
      read -p "Continue with failover? (y/N): " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Failover cancelled by user."
        exit 0
      fi
    fi
  else
    log "WARN" "Cannot determine primary database status (may indicate failure)"
  fi
}

# Promote DR replica
promote_dr_replica() {
  log "INFO" "Promoting DR replica to primary..."

  if $DRY_RUN; then
    log "INFO" "[DRY-RUN] Would promote iabank-dr-replica in us-west-2"
    return 0
  fi

  local promotion_start=$(date +%s)

  if aws rds promote-read-replica \
    --db-instance-identifier iabank-dr-replica \
    --region us-west-2 &>> "$LOG_FILE"; then

    log "INFO" "Promotion initiated successfully"

    # Wait for promotion to complete
    log "INFO" "Waiting for promotion to complete..."
    local timeout=1800  # 30 minutes
    local elapsed=0

    while [[ $elapsed -lt $timeout ]]; do
      local status=$(aws rds describe-db-instances \
        --db-instance-identifier iabank-dr-replica \
        --region us-west-2 \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null)

      if [[ "$status" == "available" ]]; then
        local promotion_time=$(($(date +%s) - promotion_start))
        log "INFO" "Promotion completed in ${promotion_time}s ✅"
        return 0
      fi

      log "INFO" "Promotion status: $status (${elapsed}s elapsed)"
      sleep 30
      elapsed=$((elapsed + 30))
    done

    error_exit "Promotion timeout after ${timeout}s"
  else
    error_exit "Failed to promote DR replica"
  fi
}

# Deploy application in DR region
deploy_dr_application() {
  log "INFO" "Deploying application stack in DR region..."

  if $DRY_RUN; then
    log "INFO" "[DRY-RUN] Would deploy Terraform stack in DR region"
    return 0
  fi

  local terraform_dir="$SCRIPT_DIR/../../../infrastructure/terraform"

  if [[ ! -d "$terraform_dir" ]]; then
    error_exit "Terraform directory not found: $terraform_dir"
  fi

  cd "$terraform_dir"

  # Initialize and select workspace
  if ! terraform init &>> "$LOG_FILE"; then
    error_exit "Terraform init failed"
  fi

  if ! terraform workspace select dr 2>/dev/null; then
    log "INFO" "Creating DR workspace..."
    terraform workspace new dr &>> "$LOG_FILE" || error_exit "Failed to create DR workspace"
  fi

  # Plan and apply
  if ! terraform plan -out=dr-deployment.tfplan &>> "$LOG_FILE"; then
    error_exit "Terraform plan failed"
  fi

  if ! terraform apply -auto-approve dr-deployment.tfplan &>> "$LOG_FILE"; then
    error_exit "Terraform apply failed"
  fi

  log "INFO" "Application deployment completed ✅"
}

# Verify DR environment
verify_dr_environment() {
  log "INFO" "Verifying DR environment health..."

  local health_url="https://api.iabank.com/health/"
  local max_attempts=10
  local attempt=1

  while [[ $attempt -le $max_attempts ]]; do
    log "INFO" "Health check attempt $attempt/$max_attempts"

    if curl -f -s --max-time 30 "$health_url" &>> "$LOG_FILE"; then
      log "INFO" "Health check passed ✅"
      return 0
    fi

    if [[ $attempt -eq $max_attempts ]]; then
      error_exit "Health check failed after $max_attempts attempts"
    fi

    log "WARN" "Health check failed, retrying in 30s..."
    sleep 30
    attempt=$((attempt + 1))
  done
}

# Generate failover report
generate_report() {
  local end_time=$(date +%s)
  local total_time=$((end_time - START_TIME))
  local rto_minutes=$((total_time / 60))

  log "INFO" "=== FAILOVER REPORT ==="
  log "INFO" "Start time: $(date -d @$START_TIME)"
  log "INFO" "End time: $(date -d @$end_time)"
  log "INFO" "Total RTO: ${total_time}s (${rto_minutes}m)"
  log "INFO" "Log file: $LOG_FILE"

  if [[ $rto_minutes -lt 240 ]]; then  # < 4 hours
    log "INFO" "RTO target achieved ✅ (< 4 hours)"
  else
    log "WARN" "RTO target exceeded ⚠️ (≥ 4 hours)"
  fi
}

# Notification function
send_notification() {
  local status=$1
  local message=$2

  # In a real environment, this would send notifications
  # via SNS, Slack, email, etc.
  log "INFO" "NOTIFICATION [$status]: $message"
}

# Main execution
main() {
  log "INFO" "🚨 IABANK DISASTER RECOVERY FAILOVER INITIATED"
  log "INFO" "Script: $0"
  log "INFO" "Mode: $([ $DRY_RUN = true ] && echo 'DRY-RUN' || echo 'PRODUCTION')"
  log "INFO" "Log: $LOG_FILE"

  # Send start notification
  send_notification "START" "DR failover procedure initiated"

  # Execute failover steps
  check_prerequisites
  validate_primary_status
  promote_dr_replica
  deploy_dr_application
  verify_dr_environment

  # Generate report and notify success
  generate_report
  send_notification "SUCCESS" "DR failover completed successfully in ${total_time}s"

  log "INFO" "✅ FAILOVER COMPLETED SUCCESSFULLY"
  echo "🎉 DR Failover completed! Check log: $LOG_FILE"
}

# Trap errors
trap 'error_exit "Unexpected error occurred at line $LINENO"' ERR

# Execute main function
main "$@"