#!/bin/sh
# For production images delete all uneeded admin commands and remove dangerous commands.
# addgroup, adduser and chmod will be removed in entrypoint.sh during first start
# su-exec will be needed for ever restart of the cotainer
if [ "$environment" = "production" ] ; then \
  find /sbin /usr/sbin  ! -type d \
  -a ! -name addgroup \
  -a ! -name adduser \
  -a ! -name nologin \
  -a ! -name su-exec \
   -delete; \
  find /bin /usr/bin -xdev \( \
  -name chgrp -o \
  -name chmod -o \
  -name hexdump -o \
  -name ln -o \
  -name od -o \
  -name strings -o \
  -name su -o \
  \) -delete  \
; fi
