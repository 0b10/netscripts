install_dir = /opt/netscripts
install_dir_pattern = \/opt\/netscripts
launcher_dir = /rw/config/qubes-firewall.d
launcher_script = ${launcher_dir}/97_netscript-rules

install-config:
	-mv config.json /etc/netscripts.json
	-chmod 660 /etc/netscripts.json

install-daemon:
	mkdir -p ${install_dir}/

	cp daemon/netscripts-daemon.py ${install_dir}/
	cp daemon/netscripts.service /usr/lib/systemd/system/

	chown -R root:root /etc/netscripts.json ${install_dir}/ /usr/lib/systemd/system/netscripts.service
	chmod 640 /usr/lib/systemd/system/netscripts.service
	chmod -R 770 ${install_dir}

	systemctl enable netscripts.service

install-deps:
	dnf install --assumeyes ipset bind-utils python3-inotify_simple

install-scripts:
	mkdir -p ${install_dir}
	cp get-config.py reject-domain.sh reject-http.sh whitelist-dst-set.sh allow-local-resolver.sh ${install_dir}
	chmod -R 770 ${install_dir}

install-template: install-deps install-daemon install-scripts install-config

install-appvm:
	mkdir -p ${launcher_dir}
	cp set-vpn.sh ${launcher_script}
	chown root:root ${launcher_script}
	chmod 660 ${launcher_script}
	sed -i 's/dirname $$0/${install_dir_pattern}/' ${launcher_script}