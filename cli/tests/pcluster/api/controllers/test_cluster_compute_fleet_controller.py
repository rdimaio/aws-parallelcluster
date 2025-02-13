#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
#  with the License. A copy of the License is located at http://aws.amazon.com/apache2.0/
#  or in the "LICENSE.txt" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
import json
from datetime import datetime

import pytest
from assertpy import assert_that, soft_assertions

from pcluster.aws.common import AWSClientError, StackNotFoundError
from pcluster.utils import to_iso_timestr, to_utc_datetime


def cfn_describe_stack_mock_response(scheduler, stack_status="CREATE_COMPLETE"):
    return {
        "StackId": "arn:aws:cloudformation:us-east-1:123:stack/pcluster3-2/123",
        "StackName": "clustername",
        "StackStatus": stack_status,
        "Outputs": [],
        "Parameters": [{"ParameterKey": "Scheduler", "ParameterValue": scheduler}],
        "Tags": [
            {"Key": "parallelcluster:version", "Value": "3.0.0"},
        ],
    }


class TestUpdateComputeFleetStatus:
    url = "/v3/clusters/{cluster_name}/computefleet"
    method = "PATCH"

    def _send_test_request(self, client, cluster_name="clustername", region="us-east-1", request_body=None):
        query_string = []
        if region:
            query_string.append(("region", region))

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        return client.open(
            self.url.format(cluster_name=cluster_name),
            method=self.method,
            headers=headers,
            query_string=query_string,
            data=json.dumps(request_body) if request_body else None,
        )

    @pytest.mark.parametrize(
        "scheduler, status, last_status_updated_time",
        [
            ("slurm", "STOP_REQUESTED", datetime.now()),
            ("slurm", "START_REQUESTED", datetime.now()),
            ("awsbatch", "ENABLED", None),
            ("awsbatch", "DISABLED", None),
        ],
    )
    def test_successful_request(self, mocker, client, scheduler, status, last_status_updated_time):
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack", return_value=cfn_describe_stack_mock_response(scheduler)
        )
        config_mock = mocker.patch("pcluster.models.cluster.Cluster.config")
        config_mock.scheduling.scheduler = scheduler
        if scheduler == "slurm":
            if status == "UNKNOWN":
                dynamodb_item = {}  # Test dynamodb item not exist
            else:
                dynamodb_item = {"Item": {"Status": status}}
                if last_status_updated_time:
                    last_status_updated_time = str(last_status_updated_time)
                    dynamodb_item["Item"]["LastUpdatedTime"] = last_status_updated_time
            # mock the method to check the status before update
            mocker.patch("pcluster.aws.dynamo.DynamoResource.get_item", return_value=dynamodb_item)
            # mock the method to update the item in dynamodb
            mocker.patch("pcluster.aws.dynamo.DynamoResource.put_item")
        elif scheduler == "awsbatch":
            mocker.patch("pcluster.aws.batch.BatchClient.get_compute_environment_state", return_value=status)
            if status == "ENABLED":
                mocker.patch("pcluster.aws.batch.BatchClient.enable_compute_environment")
            elif status == "DISABLED":
                mocker.patch("pcluster.aws.batch.BatchClient.disable_compute_environment")
        response = self._send_test_request(client, request_body={"status": status})
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(200)
            expected_response = {"status": status}
            if last_status_updated_time:
                expected_response["lastStatusUpdatedTime"] = to_iso_timestr(to_utc_datetime(last_status_updated_time))
            assert_that(response.get_json()).is_equal_to(expected_response)

    @pytest.mark.parametrize(
        "params, scheduler, request_body, expected_response",
        [
            (
                {"region": "eu-west-"},
                "slurm",
                {"status": "STOP_REQUESTED"},
                {"message": "Bad Request: invalid or unsupported region 'eu-west-'"},
            ),
            (
                {"region": None},
                "slurm",
                {"status": "START_REQUESTED"},
                {"message": "Bad Request: region needs to be set"},
            ),
            (
                {"region": "us-east-1"},
                "slurm",
                {"status": "RUNNING"},
                {
                    "message": "Bad Request: 'RUNNING' is not one of "
                    "['START_REQUESTED', 'STOP_REQUESTED', 'ENABLED', 'DISABLED'] - 'status'"
                },
            ),
            (
                {"region": "us-east-1"},
                "slurm",
                {"status": "ENABLED"},
                {
                    "message": "Bad Request: the update compute fleet status can only be set to"
                    " `START_REQUESTED` or `STOP_REQUESTED` for Slurm clusters."
                },
            ),
            (
                {"region": "us-east-1"},
                "awsbatch",
                {"status": "START_REQUESTED"},
                {
                    "message": "Bad Request: the update compute fleet status can only be set to"
                    " `ENABLED` or `DISABLED` for AWS Batch clusters."
                },
            ),
            (
                {"region": "us-east-1"},
                "slurm",
                {"status": None},
                {
                    "message": "Bad Request: None is not one of "
                    "['START_REQUESTED', 'STOP_REQUESTED', 'ENABLED', 'DISABLED'] - 'status'"
                },
            ),
            (
                {"region": "us-east-1"},
                "slurm",
                None,
                {"message": "Bad Request: request body is required"},
            ),
        ],
    )
    def test_malformed_request(self, mocker, client, params, scheduler, request_body, expected_response):
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack", return_value=cfn_describe_stack_mock_response(scheduler)
        )
        response = self._send_test_request(client, **params, request_body=request_body)
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(400)
            assert_that(response.get_json()).is_equal_to(expected_response)

    @pytest.mark.parametrize(
        "stack_status, scheduler, request_body, expected_response",
        [
            (
                "CREATE_IN_PROGRESS",
                "slurm",
                {"status": "STOP_REQUESTED"},
                {
                    "message": "Bad Request: Failed when stopping compute fleet with error: Cannot stop/disable"
                    " compute fleet while stack is in CREATE_IN_PROGRESS status."
                },
            ),
            (
                "CREATE_FAILED",
                "slurm",
                {"status": "STOP_REQUESTED"},
                {
                    "message": "Bad Request: Failed when stopping compute fleet with error: "
                    "Cannot stop/disable compute fleet while stack is in CREATE_FAILED status."
                },
            ),
            (
                "DELETE_IN_PROGRESS",
                "awsbatch",
                {"status": "ENABLED"},
                {
                    "message": "Bad Request: Failed when starting compute fleet with error: "
                    "Cannot start/enable compute fleet while stack is in DELETE_IN_PROGRESS status."
                },
            ),
        ],
    )
    def test_bad_request_on_unstable_stack(
        self, mocker, client, stack_status, scheduler, request_body, expected_response
    ):
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack",
            return_value=cfn_describe_stack_mock_response(scheduler, stack_status),
        )
        config_mock = mocker.patch("pcluster.models.cluster.Cluster.config")
        config_mock.scheduling.scheduler = scheduler
        response = self._send_test_request(client, request_body=request_body)
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(400)
            assert_that(response.get_json()).is_equal_to(expected_response)

    @pytest.mark.parametrize(
        "current_status, target_status, expected_response",
        [
            (
                "RUNNING",
                "STOP_REQUESTED",
                {
                    "message": "Bad Request: Failed when stopping compute fleet due to "
                    "a concurrent update of the status. Please retry the operation."
                },
            ),
            (
                "STOPPED",
                "START_REQUESTED",
                {
                    "message": "Bad Request: Failed when starting compute fleet due to "
                    "a concurrent update of the status. Please retry the operation."
                },
            ),
        ],
    )
    def test_concurrent_update_bad_request(self, mocker, client, current_status, target_status, expected_response):
        """Test when the dynamodb put_item request generates concurrent issue exception."""
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack",
            return_value=cfn_describe_stack_mock_response("slurm"),
        )
        config_mock = mocker.patch("pcluster.models.cluster.Cluster.config")
        config_mock.scheduling.scheduler = "slurm"
        dynamodb_item = {"Item": {"Status": current_status}}
        last_status_updated_time = str(datetime.now())
        dynamodb_item["Item"]["Last_status_updated_time"] = last_status_updated_time
        mocker.patch("pcluster.aws.dynamo.DynamoResource.get_item", return_value=dynamodb_item)
        mocker.patch(
            "pcluster.aws.dynamo.DynamoResource.put_item",
            side_effect=AWSClientError(
                function_name="put_item",
                message="Conditional Check Failed message from boto3",
                error_code=AWSClientError.ErrorCode.CONDITIONAL_CHECK_FAILED_EXCEPTION.value,
            ),
        )
        response = self._send_test_request(client, request_body={"status": target_status})
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(400)
            assert_that(response.get_json()).is_equal_to(expected_response)


class TestDescribeComputeFleet:
    url = "/v3/clusters/{cluster_name}/computefleet"
    method = "GET"

    def _send_test_request(self, client, cluster_name="clustername", region="us-east-1"):
        query_string = []
        if region:
            query_string.append(("region", region))

        headers = {
            "Accept": "application/json",
        }
        return client.open(
            self.url.format(cluster_name=cluster_name), method=self.method, headers=headers, query_string=query_string
        )

    @pytest.mark.parametrize(
        "scheduler, status, last_status_updated_time",
        [
            ("slurm", "RUNNING", datetime.now()),
            ("slurm", "STOPPED", datetime.now()),
            ("slurm", "STOPPING", datetime.now()),
            ("slurm", "STARTING", datetime.now()),
            ("slurm", "STOP_REQUESTED", datetime.now()),
            ("slurm", "START_REQUESTED", datetime.now()),
            ("slurm", "PROTECTED", datetime.now()),
            ("slurm", "UNKNOWN", None),
            ("awsbatch", "ENABLED", None),
            ("awsbatch", "DISABLED", None),
        ],
    )
    def test_successful_request(self, mocker, client, scheduler, status, last_status_updated_time):
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack", return_value=cfn_describe_stack_mock_response(scheduler)
        )
        if scheduler == "slurm":
            if status == "UNKNOWN":
                dynamodb_item = {}  # Test dynamodb item not exist
            else:
                dynamodb_item = {"Item": {"Status": status}}
                if last_status_updated_time:
                    last_status_updated_time = str(last_status_updated_time)
                    dynamodb_item["Item"]["LastUpdatedTime"] = last_status_updated_time
            mocker.patch("pcluster.aws.dynamo.DynamoResource.get_item", return_value=dynamodb_item)
        elif scheduler == "awsbatch":
            mocker.patch("pcluster.aws.batch.BatchClient.get_compute_environment_state", return_value=status)
        response = self._send_test_request(client)
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(200)
            expected_response = {"status": status}
            if last_status_updated_time:
                expected_response["lastStatusUpdatedTime"] = to_iso_timestr(to_utc_datetime(last_status_updated_time))
            assert_that(response.get_json()).is_equal_to(expected_response)

    def test_slurm_dynamo_table_not_exist(self, mocker, client):
        """When stack exists but the dynamodb table to store the status does not exist, the status should be UNKNOWN."""
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack", return_value=cfn_describe_stack_mock_response("slurm")
        )
        mocker.patch(
            "pcluster.aws.dynamo.DynamoResource.get_item",
            side_effect=AWSClientError(
                function_name="get_item",
                message="An error occurred (ResourceNotFoundException) when"
                " calling the GetItem operation: Requested resource not found",
            ),
        )
        response = self._send_test_request(client)
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(200)
            expected_response = {"status": "UNKNOWN"}
            assert_that(response.get_json()).is_equal_to(expected_response)

    @pytest.mark.parametrize(
        "scheduler, stack_status", [("slurm", "CREATE_IN_PROGRESS"), ("awsbatch", "DELETE_IN_PROGRESS")]
    )
    def test_unknown_status_on_unstable_stack(self, mocker, client, scheduler, stack_status):
        """When stack is in unstable status, the status should be UNKNOWN."""
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack",
            return_value=cfn_describe_stack_mock_response(scheduler, stack_status),
        )
        response = self._send_test_request(client)
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(200)
            expected_response = {"status": "UNKNOWN"}
            assert_that(response.get_json()).is_equal_to(expected_response)

    @pytest.mark.parametrize(
        "params, expected_response",
        [
            (
                {"region": "eu-west-"},
                {"message": "Bad Request: invalid or unsupported region 'eu-west-'"},
            ),
            (
                {"region": None},
                {"message": "Bad Request: region needs to be set"},
            ),
        ],
    )
    def test_malformed_request(self, client, params, expected_response):
        response = self._send_test_request(client, **params)
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(400)
            assert_that(response.get_json()).is_equal_to(expected_response)

    def test_stack_not_exist_request(self, mocker, client):
        mocker.patch(
            "pcluster.aws.cfn.CfnClient.describe_stack",
            side_effect=StackNotFoundError(function_name="describestack", stack_name="stack_name"),
        )
        response = self._send_test_request(client)
        with soft_assertions():
            assert_that(response.status_code).is_equal_to(404)
            assert_that(response.get_json()).is_equal_to(
                {
                    "message": "Cluster 'clustername' does not exist or belongs to an "
                    "incompatible ParallelCluster major version."
                }
            )
