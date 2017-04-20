#!/bin/bash


SRC_PATH=./eee_linuxserver
DEST_PATH=./linuxserver
CLS_PATH=./linuxserver/XCLS/cls_cfg.txt

cp -rf ${SRC_PATH}/* ${DEST_PATH}

sed -i '/addr4Client\s=[^:]*/s/addr4Client\s=[^:]*/addr4Client = localhost/g' ${CLS_PATH}
