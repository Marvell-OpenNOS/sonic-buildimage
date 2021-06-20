#!/bin/bash

PRE_BUILT_TARGET_DIR=$1

declare -a pkgs=("grpcio==1.38.0" "grpcio-tools==1.20.0" "m2crypto==0.36.0" "bitarray==1.5.3" "lxml==4.6.3")

rm -rf $PRE_BUILT_TARGET_DIR && mkdir $PRE_BUILT_TARGET_DIR

for pkg in "${pkgs[@]}"
do
    rm -rf wheel-download
    mkdir -p wheel-download/sources && pip3 download --platform linux_armv7l --no-deps --dest wheel-download $pkg
    count=`ls -1 wheel-download/*.gz  2>/dev/null | wc -l`
    if [ $count != 0 ]
    then 
        tar xvf  wheel-download/*.gz -C wheel-download/sources
        pushd wheel-download/sources/* && CC=$CC LDSHARED="$CC -shared" python3 -u -c "import setuptools, tokenize;__file__='setup.py';f=getattr(tokenize, 'open', open)(__file__);code=f.read().replace('\ri\n', '\n');f.close();exec(compile(code, __file__, 'exec'))" --verbose bdist_wheel --plat-name linux_armv7l -d ../../../$PRE_BUILT_TARGET_DIR && popd
    else
        cp wheel-download/*.whl $PRE_BUILT_TARGET_DIR
    fi 

    rm -rf wheel-download

    mkdir -p wheel-download/sources && pip download --platform linux_armv7l --no-deps --dest wheel-download $pkg
    count=`ls -1 wheel-download/*.gz  2>/dev/null | wc -l`
    if [ $count != 0 ]
    then 
        tar xvf  wheel-download/*.gz -C wheel-download/sources
        pushd wheel-download/sources/* && CC=$CC LDSHARED="$CC -shared" python -u -c "import setuptools, tokenize;__file__='setup.py';f=getattr(tokenize, 'open', open)(__file__);code=f.read().replace('\ri\n', '\n');f.close();exec(compile(code, __file__, 'exec'))" --verbose bdist_wheel --plat-name linux_armv7l -d ../../../$PRE_BUILT_TARGET_DIR && popd
    else
        cp wheel-download/*.whl $PRE_BUILT_TARGET_DIR/
    fi 

    rm -rf wheel-download 

done

