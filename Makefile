install-daemon:
	sudo mkdir -p /opt/netscripts/

	sudo cp config.json /etc/netscripts.json
	sudo cp daemon/netscripts-daemon.py /opt/netscripts/
	sudo cp daemon/netscripts.service /usr/lib/systemd/system/

	sudo chown -R root:root /etc/netscripts.json /opt/netscripts/ /usr/lib/systemd/system/netscripts.service
	sudo chmod 660 /etc/netscripts.json
	sudo chmod 640 /usr/lib/systemd/system/netscripts.service
	sudo chmod -R 770 /opt/netscripts

	sudo systemctl enable netscripts.service

install-deps:
	sudo dnf install --assumeyes ipset bind-utils python3-inotify_simple

install: install-deps install-daemon