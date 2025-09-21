#!/bin/bash
rm -f lambda_create.zip lambda_redirect.zip
cd lambda_create && zip -r ../lambda_create.zip . && cd ..
cd lambda_redirect && zip -r ../lambda_redirect.zip . && cd ..
