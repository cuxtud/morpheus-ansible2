patching
=========

This role updates the system ( Redhat or Centos ) as follows:

1- Prechecks like Repository checks, and gather all your mandatory checks information(mount,ip details,routing,services,etc)
2- if repository is success, patch the server
3- if patch the server reboot.
4- wait for  server booting, once back and validate your server with your precheck data.


Role Variables
--------------
The variables that can be passed to this role are as follows:
supported_distros:
  - Redhat
  - CentOS

/tmp/services-{{ inventory_hostname }}.yml	# the file that contains the service should be running on the system



Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

---
    - hosts:  servers
      roles:
        - patching


License
-------

BSD

Author Information
------------------

#############################################
#For Help Contact me : "Ahmed Hagag"
#
#     ahmed.thagag@gmail.com
#############################################
