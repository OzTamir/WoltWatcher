echo 'Stopping...'
sh ./stop.sh
echo 'Pulling...'
git pull
echo 'Building...'
sh ./build.sh
echo 'Running...'
sh ./run.sh