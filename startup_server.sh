git stash
git pull || true
git stash pop
sudo ./install_new_dependencies.sh
sudo python3 joycon_server.py &
sudo ./execute_follow_up_projects.sh &