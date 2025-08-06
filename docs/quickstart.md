

# Quick Start

This guide will get you up and running with BorgDash in just a few minutes.

The recommended way to run BorgDash is running the container with docker.

## Run BorgDash with Docker Compose

1. Make sure you have Docker installed.
2. Download the latest [docker-compose.yaml](https://raw.githubusercontent.com/hbrennhaeuser/BorgDash/main/docker-compose.yml):
   ```bash
   curl -O https://raw.githubusercontent.com/hbrennhaeuser/BorgDash/main/docker-compose.yml
   ```
3. Start BorgDash:
   ```bash
   docker compose up -d
   ```
4. Open [http://yourserver:5680](http://yourserver:5680) in your browser.



## Server Configuration

Configuration is currently only possible via configuration files.
If you are using Docker, you can edit the files directly in the volume or log into the container with
```bash
docker exec -it <containername> /bin/bash
```
(`vi` is available inside the container).

For more details, see the [configuration documentation](configuration.md).


## Server Job Configuration

To allow clients to send information to the BorgDash API, you need to configure a job on the server.

See the [job configuration guide](configuration.md#job-configuration).


## Client (borg/borgmatic) Configuration

On the client running borg or borgmatic, you can use the provided borgmatic hook script or the borg wrapper script to send status information to the BorgDash server.

For more information, see the [configuration documentation](configuration.md#client-configuration).
