#!/bin/bash


SRC_PATH=./eee_linuxserver
DEST_PATH=./linuxserver
CLS_PATH=./linuxserver/XCLS/cls_cfg.txt
DB_PATH=./db
SHM_DUMP_PATH=./linuxserver/XSHMSVR/Dump
DATE="`date +%Y-%m-%d_%H-%M-%S`"

NEW_DB_PATH="${DB_PATH}_${DATE}"
NEW_SHM_DUMP_PATH="${SHM_DUMP_PATH}_${DATE}"


mv ${NEW_DB_PATH} ${NEW_DB_PATH}
mv ${SHM_DUMP_PATH} ${NEW_SHM_DUMP_PATH}

