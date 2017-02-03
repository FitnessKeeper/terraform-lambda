terraform-apply-lambda
======================

A way to run ``terraform apply`` inside an AWS Lambda function.

Motivation
----------

We use `Terraform <https://www.terraform.io/>`_ to manage our infrastructure.
Creating the plan files can be done anywhere -- we use Circle CI -- but
actually applying the plan file requires powerful administrative permissions.

By running the ``apply`` step inside AWS itself, we don't have to create and
manage keys for these permissions -- and so there's no risk of these keys
being lost or leaked.  With a Lambda function, we just use IAM roles, and
never have to do explicit key management.

Installation
------------

1. In the Lambda section of your AWS Console, create a new, blank Lambda
   function.

2. Add an S3 PUT trigger to your Lambda that fires whenever you upload a
   new Terraform plan file.

3. Select the "Python 2.7" runtime, then copy and paste the code in
   ``service.py`` into the code editor.

License
-------

MIT license.
