#!/bin/bash

#### Log the execution to a file ####

exec 3>&1 4>&2

trap 'exec 2>&4 1>&3' 0 1 2 3 RETURN

exec 1>/var/log/configure-bastion.log 2>&1

sudo yum -y install java-1.8.0-openjdk

sudo yum -y install wget

wget -P /usr/local/boomi https://platform.boomi.com/atom/atom_install64.sh && chmod +x /usr/local/boomi/atom_install64.sh

AuthType=${boomiAuthenticationType}
AuthType=$(echo "$AuthType" | tr '[:lower:]' '[:upper:]')
if [ $AuthType = TOKEN ]
then
 TOKEN="$(gsutil cat gs://${DeploymentName}-bucket/token.txt | head -1 | base64 --decode)"
 gsutil rm gs://${DeploymentName}-bucket/token.txt
 sudo /usr/local/boomi/atom_install64.sh -q console -VinstallToken=$TOKEN -VatomName=${AtomName} -VaccountId=${boomiAccountID} -dir "/opt/boomi/"        
else
 Password="$(gsutil cat gs://${DeploymentName}-bucket/token.txt | head -1 | base64 --decode)"
 sudo /usr/local/boomi/atom_install64.sh -q console -Vusername=${boomiUserEmailID} -Vpassword=$Password -VatomName=${AtomName} -VaccountId=${boomiAccountID} -dir "/opt/boomi/"        
fi
