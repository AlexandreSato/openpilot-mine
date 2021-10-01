#!/usr/bin/bash -e

# git diff --name-status origin/release3-staging | grep "^A" | less

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

cd $DIR

BUILD_DIR=/data/openpilot
SOURCE_DIR="$(git rev-parse --show-toplevel)"

BRANCH=release3-staging

# set git identity
source $DIR/identity.sh

echo "[-] Setting up repo T=$SECONDS"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR
cd $BUILD_DIR
git init
git remote add origin git@github.com:commaai/openpilot.git
git checkout -f -B $BRANCH

# do the files copy
echo "[-] copying files T=$SECONDS"
cd $SOURCE_DIR
cp -pR --parents $(cat release/files_common) $BUILD_DIR/
cp -pR --parents $(cat release/files_tici) $BUILD_DIR/

# in the directory
cd $BUILD_DIR

rm -f panda/board/obj/panda.bin.signed

VERSION=$(cat selfdrive/common/version.h | awk -F[\"-]  '{print $2}')
echo "#define COMMA_VERSION \"$VERSION-release\"" > selfdrive/common/version.h

echo "[-] committing version $VERSION T=$SECONDS"
git add -f .
git commit -a -m "openpilot v$VERSION release"

# Build panda firmware
pushd panda/
CERT=/data/pandaextra/certs/release RELEASE=1 scons -u .
mv board/obj/panda.bin.signed /tmp/panda.bin.signed
popd

# Build
export PYTHONPATH="$BUILD_DIR"
scons -j$(nproc)

# Run tests
#python selfdrive/manager/test/test_manager.py
selfdrive/car/tests/test_car_interfaces.py

# Cleanup
find . -name '*.a' -delete
find . -name '*.o' -delete
find . -name '*.os' -delete
find . -name '*.pyc' -delete
find . -name '__pycache__' -delete
rm -rf panda/board panda/certs panda/crypto
rm -rf .sconsign.dblite Jenkinsfile release/
rm models/supercombo.dlc

# Move back signed panda fw
mkdir -p panda/board/obj
mv /tmp/panda.bin.signed panda/board/obj/panda.bin.signed

# Restore phonelibs
git checkout phonelibs/

# Mark as prebuilt release
touch prebuilt

# Add built files to git
git add -f .
git commit --amend -m "openpilot v$VERSION"

if [ ! -z "$PUSH" ]; then
  echo "[-] pushing T=$SECONDS"
  git remote set-url origin git@github.com:commaai/openpilot.git
  git push -f origin $BRANCH

  # Create dashcam
  git rm selfdrive/car/*/carcontroller.py
  git commit -m "create dashcam release from release"
  git push -f origin $BRANCH:dashcam3-staging
fi

echo "[-] done T=$SECONDS"
