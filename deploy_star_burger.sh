#!/bin/bash

set -e

cd /opt/star-burger/
source .env
git pull
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
source venv/bin/activate
pip3 install -r requirements.txt
python3 manage.py collectstatic --no-input
python3 manage.py migrate --no-input
systemctl restart star-burger.service
http https://api.rollbar.com/api/1/deploy X-Rollbar-Access-Token:$ROLLBAR_TOKEN environment=$ROLLBAR_ENVIRONMENT revision=$(git rev-parse HEAD)
echo "Sucessfully deployed!"
