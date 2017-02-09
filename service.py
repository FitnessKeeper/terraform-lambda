# -*- coding: utf-8 -*-

import os
import subprocess
import urllib

import boto3


# Version of Terraform that we're using
TERRAFORM_VERSION = '0.8.5'

# Download URL for Terraform
TERRAFORM_DOWNLOAD_URL = (
    'https://releases.hashicorp.com/terraform/%s/terraform_%s_linux_amd64.zip'
    % (TERRAFORM_VERSION, TERRAFORM_VERSION))

# Paths where Terraform should be installed
TERRAFORM_DIR = os.path.join('/tmp', 'terraform_%s' % TERRAFORM_VERSION)
TERRAFORM_PATH = os.path.join(TERRAFORM_DIR, 'terraform')


def check_call(args):
    """Wrapper for subprocess that checks if a process runs correctly,
    and if not, prints stdout and stderr.
    """
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd='/tmp')
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print(stdout)
        print(stderr)
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            cmd=args)


def install_terraform():
    """Install Terraform on the Lambda instance."""
    # Most of a Lambda's disk is read-only, but some transient storage is
    # provided in /tmp, so we install Terraform here.  This storage may
    # persist between invocations, so we skip downloading a new version if
    # it already exists.
    # http://docs.aws.amazon.com/lambda/latest/dg/lambda-introduction.html
    if os.path.exists(TERRAFORM_PATH):
        return

    urllib.urlretrieve(TERRAFORM_DOWNLOAD_URL, '/tmp/terraform.zip')

    # Flags:
    #   '-o' = overwrite existing files without prompting
    #   '-d' = output directory
    check_call(['unzip', '-o', '/tmp/terraform.zip', '-d', TERRAFORM_DIR])

    check_call([TERRAFORM_PATH, '--version'])


def remote_config_terraform(s3_bucket):
    """Configure terraform to use remote state

    :param s3_bucket: Name of the S3 bucket where the state is stored.

    """
    check_call([
        TERRAFORM_PATH,
        'remote', 'config',
        '-backend=S3',
        '-backend-config="bucket={0}"'.format(s3_bucket),
        '-backend-config="key=terraform.tfstate'
        '-backend-config="region=eu-west-1"'
    ])


def apply_terraform_plan(s3_bucket, path):
    """Download a Terraform plan from S3 and run a 'terraform apply'.

    :param s3_bucket: Name of the S3 bucket where the plan is stored.
    :param path: Path to the Terraform planfile in the S3 bucket.

    """
    # Although the /tmp directory may persist between invocations, we always
    # download a new copy of the planfile, as it may have changed externally.
    s3 = boto3.resource('s3')
    planfile = s3.Object(s3_bucket, path)
    planfile.download_file('/tmp/terraform.plan')
    check_call([TERRAFORM_PATH, 'apply', '/tmp/terraform.plan'])


def handler(event, context):
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    path = event['Records'][0]['s3']['object']['key']

    install_terraform()
    remote_config_terraform(s3_bucket=s3_bucket)
    apply_terraform_plan(s3_bucket=s3_bucket, path=path)
