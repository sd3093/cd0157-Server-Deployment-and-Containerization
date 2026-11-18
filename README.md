# Deploying a Flask API

## Submission notes (what was done)

- **Dockerfile** - `python:stretch` base image as explicitly required by the course rubric, installs `requirements.txt`, entrypoint `["gunicorn", "-b", ":8080", "main:APP"]`. The image supplies Python 3.7.4. It is a historical, obsolete course dependency; use a maintained image for deployments outside this exercise. `.dockerignore` excludes local secrets, Git metadata, and caches from the image.
- **JWT_SECRET in a file** - `.env_file.example` holds `JWT_SECRET` and `LOG_LEVEL` for running the container locally (copy it to `.env_file`, which stays git-ignored). In the cluster the pods get `JWT_SECRET` from the Kubernetes secret `jwt-secret` (`simple_jwt_api.yml`), which CodeBuild creates from the parameter-store value.
- **buildspec.yml** - `env: parameter-store: JWT_SECRET: JWT_SECRET`; `pre_build` installs the requirements and runs `python -m pytest test_main.py`, so a failing test stops the deployment; kubectl v1.36.0 matches the EKS cluster (Kubernetes 1.36).
- **ci-cd-codepipeline.cfn.yml** - defaults set: EKS cluster `simple-jwt-api`, repo `cd0157-Server-Deployment-and-Containerization`, branch `master`, GitHub user `sd3093`, kubectl role `UdacityFlaskDeployCBKubectlRole`; CodeBuild image `aws/codebuild/standard:7.0`; custom-resource Lambda on `python3.12`.
- **test_main.py** - tests for `/`, `/auth`, `/contents` (valid, missing and invalid token).
- **trust.json / aws-auth-patch.yml / iam-role-policy.json** - IAM role `UdacityFlaskDeployCBKubectlRole` for CodeBuild and its `system:masters` mapping in the cluster's `aws-auth` ConfigMap.

### Run locally

### November 18 resubmission verification

The Docker base image now matches the exact rubric requirement. An actual
`linux/amd64` build completed successfully on Docker Desktop. All five existing
pytest checks passed inside that image. An additional HTTP probe verified `/`,
`/auth`, and `/contents` through Gunicorn, including the expected `email`, `exp`,
and `nbf` fields and HTTP 401 responses for missing/invalid tokens. The probe
also verified that the JWT signature uses the secret supplied by an env file.
See `verification/docker-build.log`, `verification/docker-pytest.log`, and
`verification/docker-http.txt`.

Reproduce the container checks from the repository root:

```bash
docker build --platform linux/amd64 -t udacity-flask-eks:resubmit-20261118 .
docker run --rm --platform linux/amd64 --entrypoint python \
  udacity-flask-eks:resubmit-20261118 -m pytest test_main.py -v
python3 scripts/verify_container.py
```

The HTTP probe creates an ephemeral test secret, binds the container only to
localhost on a free port, and removes its own test container afterward. These
local results do not establish that the separate AWS EKS deployment is healthy.

### Verified EKS deployment — November 18, 2026

Public service URL:

http://aaa3850c8b5874d358a619f5e95b137d-1697945521.us-east-2.elb.amazonaws.com/

The existing `simple-jwt-api` cluster in `us-east-2` has one Ready worker and
three Running application pods. CodeBuild build
`simple-jwt-api-pipeline:cad0b1a0-86ef-4408-a015-75aaa646282f` succeeded for source
commit `c6151ec01bf2e5a0bdb839179ce2f0c81dd3496f`, running five tests, building
`python:stretch`, publishing the image, and completing the Kubernetes rollout.

At 17:20 UTC on November 18, the public ELB returned HTTP 200 for all three
endpoints: `/` returned `Healthy`; `/auth` issued a JWT; and `/contents` returned
the expected email and valid `exp`/`nbf` fields. Missing and invalid JWTs returned
HTTP 401. The JWT itself is omitted from saved evidence.

- `verification/codebuild-success.jpg`: actual AWS build status and phases.
- `verification/codebuild-log.txt`: actual tests, image build and successful rollout.
- `verification/final-build-status.json`: AWS API build result and source commit.
- `verification/final-kubernetes-status.txt`: Ready node, three Running pods and ELB hostname.
- `verification/final-deployment.json`: three updated/ready replicas and deployed image tag.
- `verification/live-endpoints.json`: timestamped HTTP statuses and responses from the public ELB.

Recheck the deployed endpoints with:

```bash
python3 scripts/verify_live.py \
  http://aaa3850c8b5874d358a619f5e95b137d-1697945521.us-east-2.elb.amazonaws.com
```

The previous worker had failed to bootstrap while the Udacity lab was inactive.
Reactivating the lab and restarting that worker restored service without changing
IAM or organization policy. The deployment is being left running for review.
Udacity may suspend lab resources; the timestamped logs preserve the actual
successful deployment and endpoint results if that happens.

### Manual local usage

```bash
pip install -r requirements.txt
python -m pytest test_main.py

cp .env_file.example .env_file
docker build -t myimage .
docker run --name myContainer --env-file=.env_file -p 80:8080 myimage

curl http://localhost:80/
export TOKEN=`curl -s -d '{"email":"abc@xyz.com","password":"WindowsPwd"}' -H "Content-Type: application/json" -X POST localhost:80/auth | jq -r '.token'`
curl -s http://localhost:80/contents -H "Authorization: Bearer ${TOKEN}" | jq .
```

---

This is the project starter repo for the course Server Deployment, Containerization, and Testing.

In this project you will containerize and deploy a Flask API to a Kubernetes cluster using Docker, AWS EKS, CodePipeline, and CodeBuild.

The Flask app that will be used for this project consists of a simple API with three endpoints:

- `GET '/'`: This is a simple health check, which returns the response 'Healthy'. 
- `POST '/auth'`: This takes a email and password as json arguments and returns a JWT based on a custom secret.
- `GET '/contents'`: This requires a valid JWT, and returns the un-encrpyted contents of that token. 

The app relies on a secret set as the environment variable `JWT_SECRET` to produce a JWT. The built-in Flask server is adequate for local development, but not production, so you will be using the production-ready [Gunicorn](https://gunicorn.org/) server when deploying the app.



## Prerequisites

* Docker Desktop - Installation instructions for all OSes can be found <a href="https://docs.docker.com/install/" target="_blank">here</a>.
* Git: <a href="https://git-scm.com/downloads" target="_blank">Download and install Git</a> for your system. 
* Code editor: You can <a href="https://code.visualstudio.com/download" target="_blank">download and install VS code</a> here.
* AWS Account
* Python version between 3.7 and 3.9. Check the current version using:
```bash
#  Mac/Linux/Windows 
python --version
```
You can download a specific release version from <a href="https://www.python.org/downloads/" target="_blank">here</a>.

* Python package manager - PIP 19.x or higher. PIP is already installed in Python 3 >=3.4 downloaded from python.org . However, you can upgrade to a specific version, say 20.2.3, using the command:
```bash
#  Mac/Linux/Windows Check the current version
pip --version
# Mac/Linux
pip install --upgrade pip==20.2.3
# Windows
python -m pip install --upgrade pip==20.2.3
```
* Terminal
   * Mac/Linux users can use the default terminal.
   * Windows users can use either the GitBash terminal or WSL. 
* Command line utilities:
  * AWS CLI installed and configured using the `aws configure` command. Another important configuration is the region. Do not use the us-east-1 because the cluster creation may fails mostly in us-east-1. Let's change the default region to:
  ```bash
  aws configure set region us-east-2  
  ```
  Ensure to create all your resources in a single region. 
  * EKSCTL installed in your system. Follow the instructions [available here](https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html#installing-eksctl) or <a href="https://eksctl.io/introduction/#installation" target="_blank">here</a> to download and install `eksctl` utility. 
  * The KUBECTL installed in your system. Installation instructions for kubectl can be found <a href="https://kubernetes.io/docs/tasks/tools/install-kubectl/" target="_blank">here</a>. 


## Initial setup

1. Fork the <a href="https://github.com/udacity/cd0157-Server-Deployment-and-Containerization" target="_blank">Server and Deployment Containerization Github repo</a> to your Github account.
1. Locally clone your forked version to begin working on the project.
```bash
git clone https://github.com/SudKul/cd0157-Server-Deployment-and-Containerization.git
cd cd0157-Server-Deployment-and-Containerization/
```
1. These are the files relevant for the current project:
```bash
.
├── Dockerfile 
├── README.md
├── aws-auth-patch.yml #ToDo
├── buildspec.yml      #ToDo
├── ci-cd-codepipeline.cfn.yml #ToDo
├── iam-role-policy.json  #ToDo
├── main.py
├── requirements.txt
├── simple_jwt_api.yml
├── test_main.py  #ToDo
└── trust.json     #ToDo 
```

     
## Project Steps

Completing the project involves several steps:

1. Write a Dockerfile for a simple Flask API
2. Build and test the container locally
3. Create an EKS cluster
4. Store a secret using AWS Parameter Store
5. Create a CodePipeline pipeline triggered by GitHub checkins
6. Create a CodeBuild stage which will build, test, and deploy your code

For more detail about each of these steps, see the project lesson.
