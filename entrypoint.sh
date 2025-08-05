#!/bin/sh
# Entrypoint script for BorgDash Docker container

set -e

# set default for required env vars
: "${BORGDASH_CONFIG_FILE:=config.toml}"
export BORGDASH_UID="${BORGDASH_UID:-1000}"
export BORGDASH_GID="${BORGDASH_GID:-1000}"
export BORGDASH_USER="borgdash"
export BORGDASH_GROUP="borgdash"


# enforce certain env vars
export BORGDASH_CONFIG_DIR=/config
export BORGDASH_JOBS_DIR=$BORGDASH_CONFIG_DIR/jobs
export BORGDASH_CONFIG_FILE_PATH=$BORGDASH_CONFIG_DIR/$BORGDASH_CONFIG_FILE


BORGDASH_CONFIG_EXAMPLE_FILE_PATH="/app/config.example.toml"




wait_indefinetly() {
    log "Unrecoverable error detected during startup, waiting..."
    while [ ! -f "$CONFIG_FILE" ]; do
        sleep 2
    done
}

log(){
    echo "[entrypoint] $@"
}


log "$(cat <<'EOF'

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    d8888b.  .d88b.  d8888b.  d888b       d8888b.  .d8b.  .d8888. db   db 
    88  `8D .8P  Y8. 88  `8D 88' Y8b      88  `8D d8' `8b 88'  YP 88   88 
    88oooY' 88    88 88oobY' 88           88   88 88ooo88 `8bo.   88ooo88 
    88~~~b. 88    88 88`8b   88  ooo      88   88 88~~~88   `Y8b. 88~~~88 
    88   8D `8b  d8' 88 `88. 88. ~8~      88  .8D 88   88 db   8D 88   88 
    Y8888P'  `Y88P'  88   YD  Y888P       Y8888D' YP   YP `8888Y' YP   YP 
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

EOF
)"



log 'Enforcing baseline configuration and parameters'

log '- Enforcing CONFIG_DIR existence'
mkdir -p "$BORGDASH_CONFIG_DIR"


log '- Checking config file'
if [ ! -f "$BORGDASH_CONFIG_FILE_PATH" ]; then
    log "- No config.toml found, copying default config"
    cp "$BORGDASH_CONFIG_EXAMPLE_FILE_PATH" "$BORGDASH_CONFIG_FILE_PATH"
fi


log '- Enforcing JOBS_DIR existence'
mkdir -p "$BORGDASH_JOBS_DIR"

log "" 
log 'BorgDash environment variables:'
env | grep '^BORGDASH' | sort | while read line; do
    log "- $line"
done


log "" 
log "Ensuring permisisons and switching user"
if [ "$(id -u)" = 0 ]; then
    # Create group if needed
    if ! getent group "$BORGDASH_GROUP" >/dev/null; then
        log "Creating group $BORGDASH_GROUP ($BORGDASH_GID)"
        groupadd -g "$BORGDASH_GID" "$BORGDASH_GROUP"
    fi

    # Create user if needed
    if ! id -u "$BORGDASH_USER" >/dev/null 2>&1; then
        log "Creating user $BORGDASH_USER ($BORGDASH_UID)"
        useradd -m -u "$BORGDASH_UID" -g "$BORGDASH_GID" "$BORGDASH_USER"
    fi

    # Set ownership of /data and /config
    log "Setting ownership for /data /config"
    chown -R "$BORGDASH_UID:$BORGDASH_GID" /data /config || true

    # Set permissions for .toml and .json files: ug=rw, o=r
    log "Setting file permissions for .toml and .json files"
    find /data /config -type f \( -name "*.toml" -o -name "*.json" \) -exec chmod 664 {} +

    # Set permissions for directories: ug=rwx, o=rx
    log "Setting directory permissions"
    find /data /config -type d -exec chmod 775 {} +
fi



log "" 
log "Starting server..."
exec gosu "$BORGDASH_USER" "$@"
