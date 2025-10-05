# Animal Classification

Example usage of the text generation service to classify images of animals from a [sample Kaggle dataset](https://www.kaggle.com/api/v1/datasets/download/iamsouravbanerjee/animal-image-dataset-90-different-animals).
It shows how to download the dataset, transfer it to a remote environment, and run inference using different language models.

To run this example:
1. All environment variables used by the scripts are defined in `env.sh`. Before running any of the examples, load these variables into your shell: `source env.sh`
2. Download the image samples locally and upload them to your remote cluster: `./download.sh`
3. Launch the service (assuming Blackfish is already running): `./launch.sh`
4. Run the script `python main.py`

**Note** - This example assumes that Blackfish is running on a remote cluster.
Also, there is an option to use a `data:` file format for the images. However, this
requires manually converting each image to PIL data. 
