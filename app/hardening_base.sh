#!/bin/sh

rm -fr /var/spool/cron
rm -fr /etc/crontabs
rm -fr /etc/periodic

# Remove every user and group but root
sed -i -r '/^(root)/!d' /etc/group
sed -i -r '/^(root)/!d' /etc/passwd    

# Remove init scripts since we do not use them.
rm -fr /etc/inittab

# Remove kernel tunables since we do not need them.
rm -fr /etc/sysctl*
rm -fr /etc/modprobe.d

# Remove fstab since we do not need it.
rm -f /etc/fstab
