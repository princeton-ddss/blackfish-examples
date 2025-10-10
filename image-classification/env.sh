# env.sh — shared environment variables for image-classification example

# Local directory for dataset download & extraction
export LOCAL_DIR="data"

# User identity for remote transfer (NetID or cluster username)
export NETID="gl2969"

# Profile to use for Blackfish jobs 
export PROFILE="gl2969"

# Remote directory on Della
export REMOTE_DIR="/home/$NETID/image-classification-example"

# Kaggle dataset details
export KAGGLE_URL="https://www.kaggle.com/api/v1/datasets/download/iamsouravbanerjee/animal-image-dataset-90-different-animals"
export KAGGLE_KEY="$HOME/.kaggle/kaggle.json"
