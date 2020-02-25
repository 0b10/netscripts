Copy config.example.json to config.json, add your configuration options, then `make install`.

The global configuration file is `/etc/netscripts.json`.

The daemon has a systemd service file: `netscripts.service` - `systemctl start|stop netscripts`, it's enabled by default.