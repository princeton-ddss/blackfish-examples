# FuzzyLink
In his paper “Probabilistic Record Linkage Using Pretrained Text Embeddings,” Joseph Ornstein developed a probabilistic record linkage procedure (dubbed “fuzzylink”) which relies on large language models to determine if two records refer to the same entity. Though his procedure outperformed other algorithms in both precision and recall, his use of closed-source models meant that the models were (1) not free to use and (2) could be modified at any time. When a model is modified or deprecated, any results that were obtained using Ornstein’s method on that model are not fully reproducible. 

[A brief explanation of Ornstein’s method here will help motivate the example].

If you need to merge two records using a probabilistic record linkage procedure and want to do it easily, transparently, and for free, you can use Blackfish to run open source models on a HPC cluster. You will know exactly what models you are using and your results can be reproduced by anyone with access to the same model. The following tutorial will walk through all the steps you need to take to use Ornstein’s fuzzylink approach on your HPC cluster. 


## Data
The original data is available for download [here](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/7U5KEJ). The files we use here are:
```shell
ceda.RData
L2.RData
(maybe more if want to include files for measure precision/recall)
```


## Usage

### Step 1: Setting up
Let’s say you have two records: one is an L2 voter file with ~22 million registered voters from California and the second contains the names of over 9,000 candidates from public office (this is application 1 from Orstein’s paper). In order to merge the names of the candidates with their records from the L2 voter files, you’ll need the following:
- The two .RData files containing the records that you wish to link placed in the /testing/Ornstein_application1/ directory (`ceda.RData` and `L2.RData` for this example)
- Blackfish installed and setup. For instructions on how to do this, visit [the blackfish documentation](https://princeton-ddss.github.io/blackfish/latest/getting_started/)

Next, you’re going to need the fuzzylink code. Ornstein created an R package that can be installed from CRAN, but that package only works with Mistral and OpenAI models. For this example, I’ve modified Ornstein’s package to work with the vllm server used by Blackfish--clone this repository to use the updated version of fuzzylink. Move your downloaded .RData files to the /testing/Ornstein_application1/ directory.

### Step 2: Running the Services on Blackfish
Once you have the data files and fuzzylink code, you can start running your blackfish services. The fuzzylink method requires two services: one used to generate embeddings and a second regular text generation model. In your terminal (in your cloned blackfish directory), start the blackfish API:
```shell
uv run blackfish start
```
Next, in a new terminal (again, in your blackfish directory), activate the blackfish environment by typing:
```shell
source .venv/bin/activate
```
This will allow you to run blackfish commands directly and easily. To start the embedding service, type the following command, changing the api key and/or time if desired:
```shell
blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --api-key sealsaretasty --task embed
```
You can check the status and port number of this service by typing:
```shell
blackfish ls
```
The service status should change from "PENDING" to “STARTING” shortly, but will take a few minutes to change to “HEALTHY.” While waiting, you can start the second service. For the text generation model, you can pick which model you want to use, though models that are not powerful enough might cause the fuzzylink code to fail if they do not respond to queries with a strictly ‘Yes’ or ‘No’ response[^1]. To see which models you have available on Blackfish type:
```shell
blackfish model ls
```
You are going to want to pick a model that is a “text-generation” model. You can also [download your own model](https://princeton-ddss.github.io/blackfish/latest/#step-4-obtain-a-model) if you want one that is not available. For this example, we will use the meta-llama/Llama-3.3-70B-Instruct model--to start this service, type the following in the CLI:
```shell
blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00  --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct --api-key sealsaretasty --revision 6f6073b423013f6a7d4d9f39144961bfbfbc386b
```
Again, you can set the API key and time as desired, as long as the API key matches that of your embedding model. You will need to wait until this model’s status is HEALTHY before proceeding, which might take 5-10 minutes after transition to STARTING, depending on your model of choice. While those models are loading, we can hop to the next step


### Step 3: Running Fuzzylink
In testing/Ornstein_application1/File 001_link-candidates.R, first, change the “file_save_name” variable to equal the name you wish to use for your output file. You can then modify the following call to fuzzylink:
```R
df <- BLfuzzylink::fuzzylink(
 dfA = ceda,
 dfB = l2,
 by = 'fullname',
 blocking.variables = c('last', 'place', 'cntyname'),
 record_type = 'person',
 instructions = 'The first name comes from a list of candidates for public office in California. The second name comes from a voter registration file. Bear in mind that some candidates may run for office under a nickname or middle name, and some records may contain spelling errors.',
 fmla = fmla,
 learner = learner,
 openai_api_key = "sealsaretasty",
 model = "EMPTY",
 embedding_model = "EMPTY",
 embedding_port_num = 8080,
 text_gen_port_num = 8081,
 embedding_dimensions = 2048
)
```
In this function call, setting the models to `EMPTY` indicates that you are running the model locally. The `open_api_key` should match what you set as your `--api-key` when initiating the services (or can be left empty if you did not set one). `Embedding_port_num` should be the port number the embedding service is running on, and `text_gen_port_num` should be the second service’s port number; both port numbers can be seen after running `blackfish ls`. Once the port numbers, api key, and file save name have been updated, you are ready to go! Wait until the status of both your services is HEALTHY, then start an R session and simply run the 001_link-candidates file! It should take a few minutes to run and will save the results to an .RData file with the name you specified in the file_save_name variable. 

### How well the models perform
Below, we provide some basic metrics on performance for five potential models that you can use. Precision and Recall were calculated using Ornstein's L2 and California Election Data Archive (CEDA) files.

Coming soon...


[^1]: If you get the error message `Error in family$linkfun(mustart) : Argument mu must be a nonempty numeric vector`, this is because the model did not respond with a strictly ‘Yes’ or ‘No’ response. Modifying the fuzzlink prompt might solve the issue. I’ve left the prompt as-is and stuck to models that returned properly formatted responses.
