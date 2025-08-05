#!/usr/bin/env bash
# Borgmatic hook script for BorgDash monitoring

# Global variables
declare -A ARGS
ACTION=""
WHEN=""
STATE=""

# Environment variables
API_URL="$BORGDASH_API_URL"
API_KEY="$BORGDASH_API_KEY" 
JOB_NAME="$BORGDASH_JOB_NAME"
CONFIG_PATH="$BMC_CONFIG_PATH"

# Logging functions
log() {
    echo "[BorgDashHook]$1" >&2
}


# Parse arguments in key:value format
parse_arguments() {
    for arg in "$@"; do
        # Handle key:'value' with potential escaped quotes
        if [[ "$arg" =~ ^([^:]+):\'(.*)\'$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            # Handle escaped quotes
            value="${value//\\\'/\'}"
            ARGS["$key"]="$value"
        # Handle key:value
        elif [[ "$arg" =~ ^([^:]+):(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            ARGS["$key"]="$value"
        else
            log "Invalid argument format: $arg"
        fi
    done
}

# Extract mandatory and optional parameters
extract_parameters() {
    TYPE="${ARGS[type]:-}"  # before, after
    EVENT="${ARGS[event]:-}"  # everything, action
    WHEN="${ARGS[when]:-}"  # create, purge, etc.
    STATE="${ARGS[state]:-}"  # finish, fail
}

# Validate mandatory parameters
validate_parameters() {
    if [[ -z "$TYPE" || -z "$EVENT" ]]; then
        log "Mandatory parameters missing: TYPE (before, after) and EVENT (everything, action) are required"
        return 1
    fi
    
    # if [[ -z "$WHEN" ]]; then
    #     log "Mandatory parameter missing: when is required"
    #     return 1
    # fi
    
    return 0
}

# Submit borgmatic rinfo to API
submit_borgmatic_rinfo() {
    # Run borgmatic rinfo command to get JSON data
    local rinfo_data
    log "Querying borgmatic rinfo"
    if ! rinfo_data=$(timeout 120 borgmatic -c "$CONFIG_PATH" rinfo --json 2>/dev/null); then
        log "Failed to run borgmatic rinfo command"
        return 1
    fi
    
    # Construct JSON payload as string
    local payload="{\"job_id\":\"$JOB_NAME\",\"rinfo_data\":$rinfo_data}"
    
    log "Pushing rinfo to BorgDash-API"
    # Submit to API
    if ! curl -s -f -X POST "${API_URL}/api/push/borgmatic/rinfo" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1; then
        log "Failed to submit borgmatic rinfo to API"
        return 1
    fi
    
    log "Successfully submitted borgmatic rinfo"
    return 0
}

# Submit borgmatic info to API
submit_borgmatic_info() {
    # Run borgmatic info command to get JSON data
    local info_data
    log "Querying borgmatic info"
    if ! info_data=$(timeout 120 borgmatic -c "$CONFIG_PATH" info --json 2>/dev/null); then
        log "Failed to run borgmatic info command"
        return 1
    fi
    
    # Construct JSON payload as string
    local payload="{\"job_id\":\"$JOB_NAME\",\"info_data\":$info_data}"

    log "Pushing info to BorgDash-API"
    # Submit to API
    if ! curl -s -f -X POST "${API_URL}/api/push/borgmatic/info" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1; then
        log "Failed to submit borgmatic info to API"
        return 1
    fi
    
    log "Successfully submitted borgmatic info"
    return 0
}

# Push event to API
push_event() {
    local event_type="$1"
    local message="$2"
    local info_content="$3"
    local action="$4"


    # Use inline Python for JSON formatting
    local py_script="import sys, json;\n"
    py_script+="job_id = sys.argv[1]\n"
    local py_script
    read -r -d '' py_script <<'EOF'
import sys, json
job_id = sys.argv[1]
type = sys.argv[2]
message = sys.argv[3]
action = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
info = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None
data = {'job_id': job_id, 'type': type, 'message': message}
if action:
    data['extra'] = {'action': action}
if info:
    data['info'] = info
print(json.dumps(data, indent=2, ensure_ascii=False))
EOF
    if [ -n "$action" ]; then
        if [ -n "$info_content" ]; then
            json_payload=$(python3 -c "$py_script" "$JOB_NAME" "$event_type" "$message" "$action" "$info_content")
        else
            json_payload=$(python3 -c "$py_script" "$JOB_NAME" "$event_type" "$message" "$action")
        fi
    else
        if [ -n "$info_content" ]; then
            json_payload=$(python3 -c "$py_script" "$JOB_NAME" "$event_type" "$message" "" "$info_content")
        else
            json_payload=$(python3 -c "$py_script" "$JOB_NAME" "$event_type" "$message")
        fi
    fi
    

    local response=$(curl -s -w "%{http_code}" -X POST \
        "${API_URL}/api/push/event" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "$json_payload")
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log "Successfully pushed $event_type event (action: $action)"
    else
        log "Failed to push $event_type event (HTTP $http_code): $response_body"
    fi
}

# Hook: before everything
before_create() {
    log "Starting backup operations for job: $BACKUP_JOB_ID"
    
    # Prepare info with configuration summary
    local info_content=""    
    push_event "start" "Backup operations started" "$info_content" "create"
}

# Hook: after everything
after_create() {
    log "Completed backup operations for job: $BACKUP_JOB_ID"
    
    # Prepare info with completion summary
    local info_content=""    
    push_event "stop" "Backup operations completed" "$info_content" "create"

}

# Hook: after create finish (success)
after_create_finish() {
    log "Archive creation completed successfully for job: $BACKUP_JOB_ID"
    
    # Prepare info with success details
    local info_content=""    
    push_event "success" "Archive creation completed successfully" "$info_content" "create"
    }

# Hook: after create fail (error)
after_craete_fail() {
    log "Archive creation failed for job: $BACKUP_JOB_ID"
    
    # Prepare info with failure details
    local info_content=""    
    push_event "failed" "Archive creation failed" "$info_content" "create"
}

# Execute appropriate hook based on action and when
execute_hook() {
    local hook_name="${TYPE}_${EVENT}_${WHEN}"
    
    case "$hook_name" in
        "before_action_create")
            before_create
            ;;
        "after_action_create")
            # Handle create hooks based on state
            if [[ "$STATE" == "finish" ]]; then
                after_create_finish
            elif [[ "$STATE" == "fail" ]]; then
                after_create_fail
            else
                log "No specific handler for after_create with STATE=$STATE"
            fi
            after_create
            ;;
        "after_everything_")
            submit_borgmatic_rinfo
            submit_borgmatic_info
            ;;
        *)
            log "No specific handler for hook: '$hook_name'"
            ;;
    esac
}

# Main function
main() {
    # Validate environment variables
    if [[ -z "$API_URL" || -z "$API_KEY" || -z "$JOB_NAME" || -z "$CONFIG_PATH" ]]; then
        log "Missing required environment variables: BORGDASH_API_URL, BORGDASH_API_KEY, BORGDASH_JOB_NAME, BMC_CONFIG_PATH"
        exit 0
    fi
    
    # Validate config file exists
    if [[ ! -f "$CONFIG_PATH" ]]; then
        log "Borgmatic configuration file not found: '$CONFIG_PATH'"
        exit 0
    fi
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Extract parameters
    extract_parameters
    
    # Validate mandatory parameters
    if ! validate_parameters; then
        exit 0  # Always exit successfully as per requirements
    fi
    
    # Execute appropriate hook
    execute_hook
    
    # Always exit successfully
    exit 0
}

# Run main function with all arguments
main "$@"
