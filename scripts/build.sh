#!/bin/bash -e

SCRIPT_DIR=$(realpath `dirname $0`)
REPO_DIR=$(realpath $SCRIPT_DIR/..)

cd $REPO_DIR

if [ "$#" -ne 1 ]; then
    TARGET="//main/..."
else
    TARGET="//main:$1"
fi

>&2 echo "bazel build $TARGET"
bazel build $TARGET
