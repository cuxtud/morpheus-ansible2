#!/bin/bash
set -e

if [ -e "/var/opt/morpheus/vm/morpheus.env" ]; then
	source /var/opt/morpheus/vm/morpheus.env
fi

if [ -z "$ERL_COOKIE" ]; then
	echo "missing erlang cookie"
else
	echo "$ERL_COOKIE" > /.erlang.cookie
	sudo chmod 400 /.erlang.cookie
	sudo chown root:root /.erlang.cookie
	echo "$ERL_COOKIE" > /var/lib/rabbitmq/.erlang.cookie
	sudo chmod 400 /var/lib/rabbitmq/.erlang.cookie
	sudo chown rabbitmq:rabbitmq /var/lib/rabbitmq/.erlang.cookie
	echo "$ERL_COOKIE" > /root/.erlang.cookie
fi

sudo chown -R rabbitmq /var/lib/rabbitmq
sudo update-rc.d rabbitmq-server defaults
sudo service rabbitmq-server restart
