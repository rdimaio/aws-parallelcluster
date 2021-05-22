# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with
# the License. A copy of the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "LICENSE.txt" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
# limitations under the License.

PCLUSTER_NAME_MAX_LENGTH = 60
PCLUSTER_NAME_REGEX = r"^([a-zA-Z][a-zA-Z0-9-]{0,%d})$"
PCLUSTER_ISSUES_LINK = "https://github.com/aws/aws-parallelcluster/issues"

CIDR_ALL_IPS = "0.0.0.0/0"

SUPPORTED_SCHEDULERS = ["slurm", "awsbatch"]
SUPPORTED_OSES = ["alinux2", "centos7", "centos8", "ubuntu1804", "ubuntu2004"]
SUPPORTED_OSES_FOR_SCHEDULER = {"slurm": SUPPORTED_OSES, "awsbatch": ["alinux2"]}
SUPPORTED_ARCHITECTURES = ["x86_64", "arm64"]
SUPPORTED_OSES_FOR_ARCHITECTURE = {
    "x86_64": SUPPORTED_OSES,
    "arm64": ["alinux2", "ubuntu1804", "ubuntu2004", "centos8"],
}

OS_MAPPING = {
    "centos7": {"user": "centos", "root-device": "/dev/sda1"},
    "centos8": {"user": "centos", "root-device": "/dev/sda1"},
    "alinux2": {"user": "ec2-user", "root-device": "/dev/xvda"},
    "ubuntu1804": {"user": "ubuntu", "root-device": "/dev/sda1"},
    "ubuntu2004": {"user": "ubuntu", "root-device": "/dev/sda1"},
}

# Describe the list of requirements to be satisfied by the Pcluster AWS Batch CLI to manage the cluster.
# It must be in the form <package-name><comparison-operator><version>
# It can contain multiple items separated by a colon.
# i.e. aws-parallelcluster-awsbatch-cli>=2.0.0,aws-parallelcluster-awsbatch-cli<3.0.0
AWSBATCH_CLI_REQUIREMENTS = "aws-parallelcluster-awsbatch-cli<2.0.0"

FSX_SSD_THROUGHPUT = [50, 100, 200]
FSX_HDD_THROUGHPUT = [12, 40]

EBS_VOLUME_TYPE_IOPS_DEFAULT = {
    "io1": 100,
    "io2": 100,
    "gp3": 3000,
}
EBS_VOLUME_SIZE_DEFAULT = 35
EBS_VOLUME_TYPE_DEFAULT = "gp2"

DEFAULT_MAX_COUNT = 10
DEFAULT_MIN_COUNT = 0

MAX_STORAGE_COUNT = {"ebs": 5, "efs": 1, "fsx": 1, "raid": 1}

COOKBOOK_PACKAGES_VERSIONS = {
    "parallelcluster": "3.0.0",
    "cookbook": "aws-parallelcluster-cookbook-3.0.0",
    "chef": "16.13.16",
    "berkshelf": "7.2.0",
    "ami": "dev",
}

CW_LOGS_RETENTION_DAYS_DEFAULT = 14
CW_DASHBOARD_ENABLED_DEFAULT = True
CW_LOGS_ENABLED_DEFAULT = True

PCLUSTER_IMAGE_NAME_REGEX = r"^[-_A-Za-z0-9{][-_A-Za-z0-9\s:{}\.]+[-_A-Za-z0-9}]$"
PCLUSTER_IMAGE_ID_REGEX = r"^([a-zA-Z][a-zA-Z0-9-]{0,127})$"

PCLUSTER_PREFIX = "parallelcluster:"
PCLUSTER_IMAGE_NAME_TAG = f"{PCLUSTER_PREFIX}image_name"
PCLUSTER_IMAGE_ID_TAG = f"{PCLUSTER_PREFIX}image_id"
PCLUSTER_IMAGE_BUILD_STATUS_TAG = f"{PCLUSTER_PREFIX}build_status"
PCLUSTER_IMAGE_CONFIG_TAG = f"{PCLUSTER_PREFIX}build_config"
PCLUSTER_S3_IMAGE_DIR_TAG = f"{PCLUSTER_PREFIX}s3_image_dir"
PCLUSTER_S3_CLUSTER_DIR_TAG = f"{PCLUSTER_PREFIX}cluster_dir"
PCLUSTER_S3_BUCKET_TAG = f"{PCLUSTER_PREFIX}s3_bucket"
PCLUSTER_IMAGE_BUILD_LOG_TAG = f"{PCLUSTER_PREFIX}build_log"
PCLUSTER_VERSION_TAG = f"{PCLUSTER_PREFIX}version"
# PCLUSTER_APPLICATION_TAG needs to be the same as the hard coded strings in cleanup_resource.py used by Lambda function
PCLUSTER_APPLICATION_TAG = f"{PCLUSTER_PREFIX}application"
# PCLUSTER_CLUSTER_NAME_TAG needs to be the same as the hard coded strings in node package
PCLUSTER_CLUSTER_NAME_TAG = f"{PCLUSTER_PREFIX}cluster-name"
# PCLUSTER_NODE_TYPE_TAG needs to be the same as the hard coded strings in node package
PCLUSTER_NODE_TYPE_TAG = f"{PCLUSTER_PREFIX}node-type"
PCLUSTER_S3_ARTIFACTS_DICT = {
    "root_directory": "parallelcluster",
    "root_cluster_directory": "clusters",
    "source_config_name": "cluster-config.yaml",
    "config_name": "cluster-config-with-implied-values.yaml",
    "template_name": "aws-parallelcluster.cfn.yaml",
    "instance_types_data_name": "instance-types-data.json",
    "custom_artifacts_name": "artifacts.zip",
    "scheduler_resources_name": "scheduler_resources.zip",
}

IMAGEBUILDER_RESOURCE_NAME_PREFIX = "ParallelClusterImage"

PCLUSTER_S3_BUCKET_VERSION = "v1"

SUPPORTED_REGIONS = [
    "af-south-1",
    "ap-east-1",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ca-central-1",
    "cn-north-1",
    "cn-northwest-1",
    "eu-central-1",
    "eu-north-1",
    "eu-south-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "me-south-1",
    "sa-east-1",
    "us-east-1",
    "us-east-2",
    "us-gov-east-1",
    "us-gov-west-1",
    "us-west-1",
    "us-west-2",
]
