#!/usr/bin/env bash
# Sets up the EKS side of the project in AWS CloudShell (region us-east-2), from the root of this repo:
#   git clone https://github.com/sd3093/cd0157-Server-Deployment-and-Containerization.git ~/cd0157
#   cd ~/cd0157 && bash eks-lab-setup.sh 2>&1 | tee ~/eks-setup.log
# Takes about 20 minutes, almost all of it the cluster creation.
set -euo pipefail
export AWS_REGION=us-east-2
CLUSTER=simple-jwt-api
ROLE=UdacityFlaskDeployCBKubectlRole
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# 1. eksctl (CloudShell ships aws and kubectl, not eksctl)
if ! command -v eksctl > /dev/null; then
  curl -sSL https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz | tar xz -C /tmp
  mkdir -p ~/.local/bin && mv /tmp/eksctl ~/.local/bin/ && export PATH=~/.local/bin:$PATH
fi
eksctl version

# 2. EKS cluster: Kubernetes 1.36 (standard support), one t3.medium node, no NAT gateway, 20 GB disk
eksctl create cluster --name $CLUSTER --version=1.36 --region=$AWS_REGION \
  --nodes=1 --instance-types=t3.medium --node-volume-size=20 --vpc-nat-mode=Disable
kubectl get nodes

# 3. IAM role that CodeBuild assumes to run kubectl (trust.json and iam-role-policy.json from this repo)
sed -i "s/arn:aws:iam::[0-9]*:root/arn:aws:iam::$ACCOUNT:root/" trust.json
aws iam create-role --role-name $ROLE --assume-role-policy-document file://trust.json --output text --query 'Role.Arn'
aws iam put-role-policy --role-name $ROLE --policy-name eks-describe --policy-document file://iam-role-policy.json

# 4. Authorize the role in the cluster: system:masters entry in the aws-auth ConfigMap
eksctl create iamidentitymapping --cluster $CLUSTER --region $AWS_REGION \
  --arn arn:aws:iam::$ACCOUNT:role/$ROLE --group system:masters --username build
kubectl get -n kube-system configmap/aws-auth -o yaml

# 5. JWT secret in the parameter store (random value; CodeBuild reads it through buildspec.yml)
aws ssm put-parameter --name JWT_SECRET --overwrite --value "$(openssl rand -hex 24)" --type SecureString --query Version
echo "LAB SETUP DONE"
