#/bin/bash

if [ ! -d "data" ]; then
    mkdir -p data
    echo "Created data directory"
fi

wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/AK012clip.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/CA138clip.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/HI009clip.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/ID014clip.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/ME025.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/MI072clip.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/MS072.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/NM014.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/NY045.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/SC068clip.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/TN946.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/TX048clip.mp3
wget -P data https://dare.wisc.edu/wp-content/uploads/sites/1051/2017/08/WI007clip.mp3