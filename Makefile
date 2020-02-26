install_dir = /opt/netscripts
install_dir_pattern = \/opt\/netscripts
launcher_dir = /rw/config/qubes-firewall.d
launcher_script = ${launcher_dir}/97_netscript-rules

install-daemon:
	sudo mkdir -p ${install_dir}/

	sudo cp config.json /etc/netscripts.json
	sudo cp daemon/netscripts-daemon.py ${install_dir}/
	sudo cp daemon/netscripts.service /usr/lib/systemd/system/

	sudo chown -R root:root /etc/netscripts.json ${install_dir}/ /usr/lib/systemd/system/netscripts.service
	sudo chmod 660 /etc/netscripts.json
	sudo chmod 640 /usr/lib/systemd/system/netscripts.service
	sudo chmod -R 770 ${install_dir}

	sudo systemctl enable netscripts.service

install-deps:
	sudo dnf install --assumeyes ipset bind-utils python3-inotify_simple

install-scripts:
	sudo mkdir -p ${install_dir}
	sudo cp get-config.py reject-domain.sh reject-http.sh whitelist-dst-set.sh ${install_dir}
	sudo chmod -R 770 ${install_dir}

install-template: install-deps install-daemon install-scripts

install-appvm:
	sudo mkdir -p ${launcher_dir}
	sudo cp set-vpn.sh ${launcher_script}
	sudo chown root:root ${launcher_script}
	sudo chmod 660 ${launcher_script}
	sudo sed -i 's/dirname $$0/${install_dir_pattern}/' ${launcher_script}