#!/bin/bash

docker run -p 8000:8000 --env-file=".env" fastapi-react