#!/bin/bash
debenout=`dpkg -l | grep -s "debsecan"`
netout=`dpkg -l | grep -s "net-tools"`
if [ -z "$debenout" ]
then
echo "No debsecan package"
echo "" | cat > vulns.txt
else
debsecan --format detail | cat > vulns.txt
fi
if [ -z "$netout" ]
then
echo "No net-tools package"
echo "" | cat > services.txt
echo "" | cat > ips.txt
else
netstat -tulpn | cat > services.txt
ifconfig | cat > ips.txt
fi
dpkg -l | cat > packages.txt
hostnamectl | grep "Operating System" | cat > os.txt
echo "Audit script finished"
