#sudo apt-get update
sudo easy_install pip
sudo pip install ansible

ansible localhost -m git -a "repo=git://github.com/wireload/screenly-ose.git dest=/home/pi/screenly version=master" || exit
cd /home/pi/screenly/misc/ansible
ansible-playbook system.yml || exit
ansible-playbook screenly.yml || exit
