# Record Linkage
In his paper “Probabilistic Record Linkage Using Pretrained Text Embeddings,” Joseph Ornstein develops a probabilistic record linkage procedure (dubbed “Fuzzylink”) that relies on large language models to determine if two records refer to the same entity. Though his procedure outperforms other algorithms in terms of both precision and recall, his findings rely on the use of closed-source models and are therefore subject to potential cost/scaling, privacy, and replication concerns. In this example, we demonstrate how to apply the Fuzzylink method using open-source models with Blackfish.

## The Fuzzylink Algorithm
The objective of the Fuzzylink algorithm is to determine whether two records, `A` and `B`, correspond to the same entity. As outlined in the paper[^1], Ornstein's Fuzzylink algorithm involves six steps:
1. Use a model to retrieve text embeddings for the string representation of `A` and `B`.
2. Compute the cosine similarity between each pair of embedding vectors in the set `A x B`, using blocking, if possible, to improve efficiency.
3. Label a training set using a LLM to identify "true" matches for a subset of the record pairs.
4. Using the labeled data, fit a model to predict the likelihood of a match given cosine similarity.
5. Using the fitted model, estimate match probabilities for all record pairs in `A x B`. Select `N` record pairs using uncertainty sampling and label them as in Step 3; add these to the training set and repeat Step 4 and 5 until the estimated likelihoods stabilize.
6. Return all record pairs and their match probability. 

Helpfully, Ornstein shared this algorithm via the R package `fuzzylink`. Less helpfully, both the package and paper rely on closed-source models from OpenAI to perform Step 1 and 3 above. This example demonstrates how to use `fuzzylink` with *open-source[^2]* models using Blackfish and `text-generation` service.

Specifically, we will replicate Application 1 from Ornstein's paper. In this application, we're given two records: one is an L2 voter file with ~22 million registered voters from California and the second contains the names of over 9,000 candidates for public office. Our goal is to match the candidate names to entities in the voter file. 


## Running the Example

### Step 1: Setting up your environment

#### Dependencies
This example assumes you are working in an environment where Blackfish is installed and setup to work with an HPC cluster. For instructions on how to do this, visit the [Blackfish docs](https://princeton-ddss.github.io/blackfish/latest/getting_started/).

You're also going to need the fuzzylink code. Ornstein created an R package that can be installed from CRAN, but that package only works with Mistral and OpenAI models. For this example, I’ve modified Ornstein’s package to work with the vLLM server used by Blackfish--[clone this repository](https://github.com/princeton-ddss/fuzzylink-for-blackfish) to use the updated version of fuzzylink.

Finally, clone the Blackfish examples repo.

#### Data
The original data is available for download [here](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/7U5KEJ). The files used in this example are:
```shell
raw/ceda.RData
raw/L2.RData
data/candidates-merge/hand_labels.RData  # for measuring precision
data/.../recall.RData  # for measuring recall
```
Copy `ceda.RData` and `L2.RData` to the directory where you will run the example.
    

### Step 2: Running the Blackfish services
Once you have the data files and `fuzzylink` code, you can start running your Blackfish services. The Fuzzylink method requires two services: one used to generate embeddings and a second standard text generation model. In your terminal, start the blackfish API:
```shell
blackfish start
```

Next, we'll start the services in a new terminal tab/window. For this example, we'll use `meta-llama/Llama-3.3-70B-Instruct`. If this model isn't available on your cluster, you'll need to add it first: 
```shell
blackfish model add meta-llama/Llama-3.3-70B-Instruct
```

Once the model is added, you can start the required services by running the following commands:
```shell
blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --task embed --name embedding-model
blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct
```

This will prompt you for an API key (optional) and then start the services for you. You can modify this file directly to change models or else start services manually at the command line, as described below. Additionally, if you want to use an embedding specific model, you can [download one yourself](https://princeton-ddss.github.io/blackfish/latest/#step-4-obtain-a-model). A good choice is `Qwen/Qwen3-Embedding-0.6B`, which can be downloaded by running:
```shell
blackfish model add Qwen/Qwen3-Embedding-0.6B
```

To start the embedding service using one of the models already available on Blackfish, type the following command, changing the API key and/or time[^3] if desired:
```shell
blackfish run --gres 1 --mem 8 --ntasks-per-node 4 --time 01:00:00 text-generation Qwen/Qwen3-Embedding-0.6B --task embed
```

Notice that we've added a `--task embed` argument. This modifies the behavior of the text generation to generate 

You can check the status and port number of this service by typing:
```shell
blackfish ls
```
The service status should change from "PENDING" to “STARTING” shortly, but will take a few minutes to change to “HEALTHY.” While waiting, you can start the second service. For the text generation model, you can pick which model you want to use, though models that are not powerful enough might cause the fuzzylink code to fail if they do not respond to queries with a strictly ‘Yes’ or ‘No’ response[^2]. To see which models you have available on Blackfish type:
```shell
blackfish model ls
```

You are going to want to pick a model that is a “text-generation” model. You can also [download your own model](https://princeton-ddss.github.io/blackfish/latest/#step-4-obtain-a-model) if you want one that is not available. For this example, we will use the `meta-llama/Llama-3.3-70B-Instruct` model--to start this service, type the following in the CLI:
```shell
blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00  --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct --api-key sealsaretasty --revision 6f6073b423013f6a7d4d9f39144961bfbfbc386b
```
Again, you can set the API key and time as desired, as long as the API key matches that of your embedding model. You will need to wait until this model’s status is "HEALTHY" before proceeding, which might take 5-10 minutes after transition to "STARTING," depending on your model of choice. While those services are starting, we can hop to the next step.


### Step 3: Running Fuzzylink
In `001_link-candidates.R`, first, change the `file_save_name` variable to equal the name you wish to use for your output file. Similarly, modify `rdata_pathway` to be the pathway to your working directory which contains your downloaded .RData files (this will also be where the fuzzylink output gets saved). You can then modify the following call to fuzzylink[^3]:
```R
df <- BFfuzzylink::fuzzylink(
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
In this function call, setting the models to `EMPTY` indicates that you are running them locally. The `open_api_key` should match what you set as your `--api-key` when initiating the services (or can be removed/left empty if you did not set one[^4]). `Embedding_port_num` should be the port number the embedding service is running on, and `text_gen_port_num` should be the second service’s port number; both port numbers can be seen after running `blackfish ls`. Once the port numbers, api key, and file save name/pathway have been updated, you are ready to go! Wait until the status of both your services is "HEALTHY," then start an R session. Make sure your session's working directory is set to the directory containing the fuzzylink package, type `devtool::load_all()`, then simply run the 001_link-candidates file! It should take a few minutes to run and will save the results to a .RData file with the name you specified in the `file_save_name` variable. 

### Step 4: Analying the results
Below, we provide some basic metrics on performance for five potential text generation models that you can use for this process. Precision and Recall were calculated by comparing the output of fuzzylink on Ornstein's L2 and California Election Data Archive (CEDA) files with his recall and hand_labels files. Make sure you have these files downloaded if you want to measure your models' performance on this linkage process.

*It is important to note that, due to the nature of the recall file provided, some false negatives may be missing in the recall calculation.*

In `006_link-candidates.R`, update `file_save_name` to be the name of the file containing the results from running the fuzzylink code (this should match the `file_save_name` from `001_link-candidates.R`). Similarly, update `rdata_pathway` to be the full pathway to where the .RData files are being stored. Now, you can simply run this file. The precisions and recalls for various text generation models are reported below--the same embedding model was used for all. Precision is a measure of the fraction of identified matches are correct ($\\frac{true  positives}{true  positives + false  positives}$) while recall measures the fraction of matches which were identified ($\\frac{true  positives}{true  positives + false  negatives}$).

| Text Generation Model                | Precision | Recall    |
| ------------------------------------ | --------- | --------- |
| meta-llama/Llama-3.1-70B-Instruct.   | 0.9938272 | 0.9378641 |
| meta-llama/Llama-3.3-70B-Instruct    | 0.99591   | 0.938343  |
| Google/gemma-3-27b-it | 0.9898374    | 0.938343  |           |
| swiss-ai/Apertus-8B-Instruct-2509    | 0.9952038 | 0.9284116 |
| Mistralai/Mixtral-8x7B-Instruct-v0.1 | 1.000000  | 0.895082  |

In his paper, Ornstein used OpenAI for getting the embeddings and the Y/N responses. In his discussion he claimed, "Because these models are closed-source and operated by for-profit entities...the results that fuzzylink produces—including those presented in this article—are not fully reproducible." He states that, while open-source models would solve this problem, the accuracy provided by OpenAI's state-of-the-art closed source models is worth the cost and inability to reproduce his results. However, the precision and recall that we report here are not too far off Ornstien's; Orsntein's estimated precision and recall were both 95.8%. While the closed-source OpenAI models might have a higher recall, our open-source models all have higher precisions; it appears that the open-source models identify less matches than the closed-source ones. Therefore, fuzzylink using these models might miss more correct matches, but will also produce fewer incorrect matches. Overall, we believe that the performance of the open-source models is comparable to the closed-source ones used by Ornstein and worth it to get free, reproducible results!


## Details
Not all models support passing the `--task embed` argument to the `vLLM` service. Below is a list of models that work based on our testing.

| Model                                      | Dimension |
| ------------------------------------------ | --------: |
| deepseek-ai/DeepSeek-R1-Distill-Llama-70B  | 8192      |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-32B   | 5120      |
| deepseek-ai/DeepSeek-V2-Lite               | 2048      |
| deepseek-ai/DeepSeek-V2-Lite-Chat          | 2048      |
| google/gemma-3-1b-it                       | 1152      |
| meta-llama/Llama-3.1-70B-Instruct          | 8192      |
| meta-llama/Llama-3.1-8B-Instruct           | 4096      |
| meta-llama/Llama-3.2-1B-Instruct           | 2048      |
| meta-llama/Llama-3.2-3B-Instruct           | 3072      |
| meta-llama/Llama-3.3-70B-Instruct          | 8192      |
| meta-llama/Meta-Llama-3-70B-Instruct       | 8192      |
| meta-llama/Meta-Llama-3-8B-Instruct        | 4096      |
| mistralai/Mistral-7B-Instruct-v0.3         | 4096      |
| mistralai/Mixtral-8x7B-Instruct-v0.1       | 4096      | 
| Qwen/Qwen2-Audio-7B-Instruct               | 4096      | 
| Qwen/Qwen2.5-32B                           | 5120      | 
| Qwen/Qwen2.5-32B-Instruct                  | 5120      | 
| Qwen/Qwen2.5-72B                           | 8192      | 
| Qwen/Qwen2.5-72B-Instruct                  | 8192      | 
| Qwen/Qwen3-14B                             | 5120      | 
| Qwen/Qwen3-32B                             | 5120      | 
| Qwen/Qwen3-8B                              | 4096      | 
| Qwen/QwQ-32B                               | 5120      | 
| TinyLlama/TinyLlama-1.1B-Chat-v1.0         | 2048      |



[^2]: If you get the error message `Error in family$linkfun(mustart) : Argument mu must be a nonempty numeric vector`, this is because the model did not respond with a strictly ‘Yes’ or ‘No’ response. Modifying the fuzzylink prompt might solve the issue. I’ve left the prompt as-is and stuck to models that returned properly formatted responses.
[^3]: In this fuzzylink call, `embedding_dimensions` is set to 2048; this is the length of the embedding vector which the TinyLlama/TinyLlama-1.1B-Chat-v1.0 model creates. If you decide to use a different model, you may want to edit this number to have it match that model's specific embedding dimensions. A list of models with their embedding dimensions is COMING SOON.
[^4]: If you leave the api key parameter empty, the fuzzylink code will, by default, try to get an OpenAI api key from your system's environment. If you don't have one, this will cause no problems, and the local model will be able to run without an api key specified. However, if you did not set an `--api-key` when starting your services AND you have an OpenAI api key findable in your system's environment, you will likely encounter an error and will need to define an `--api-key` to use for your local models.


[^1]: "Probabilistic Record Linkage Using Pretrained Text Embeddings," Ornstein, J. T. *Political Analysis*, 2025, 1–12.

[^2]: I don't draw a distinction between "open-source" and "open-weight" models. For our purposes, the difference does not matter.

[^3]: You can also change which model you use for your embeddings if you don't want to use the `TinyLlama/TinyLlama-1.1B-Chat-v1.0` model. A list of models which are compatible with the --task embed argument is COMING SOON, or you can use an embedding model you download such as the `Qwen/Qwen3-Embedding-0.6B` model.