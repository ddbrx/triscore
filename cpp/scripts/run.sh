#!/bin/bash -e

SCRIPT_DIR=$(realpath `dirname $0`)
REPO_DIR=$(realpath $SCRIPT_DIR/..)
BUILD_SCRIPT=$SCRIPT_DIR/build.sh
PACKAGE_NAME=$1
ARGS=${@:2}
EXECUTABLE=bazel-bin/main/$PACKAGE_NAME

cd $REPO_DIR

sh $BUILD_SCRIPT $PACKAGE_NAME
time $EXECUTABLE $ARGS
