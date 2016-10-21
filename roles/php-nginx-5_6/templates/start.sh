#!/bin/bash

# Disable Strict Host checking for non interactive git clones

mkdir -p -m 0700 /root/.ssh
echo -e "Host *\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config

# Tweak nginx to match the workers to cpu's
#procs=$(cat /proc/cpuinfo |grep processor | wc -l)
#ed -i -e "'s/worker_processes 5/worker_processes' $procs/" /etc/nginx/nginx.conf

# Very dirty hack to replace variables in code with ENVIRONMENT values
#if [[ "$TEMPLATE_NGINX_HTML" != "0" ]] ; then
#  for i in $(env)
#  do
#    variable=$(echo "$i" | cut -d'=' -f1)
#    value=$(echo "$i" | cut -d'=' -f2)
#    if [[ "$variable" != '%s' ]] ; then
#      replace='\$\$_'${variable}'_\$\$'
#      find /usr/share/nginx/html -type f -exec sed -i -e 's/'${replace}'/'${value}'/g' {} \;
#    fi
#  done
#fi

# Start supervisord and services
#/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
#/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
#/usr/bin/supervisord -c /etc/supervisor/supervisord.conf

#update-rc.d supervisor defaults
sudo service php5-fpm restart
update-rc.d php5-fpm defaults
sudo service nginx restart
update-rc.d nginx defaults